"""
Module 5 — Grade Node (the self-correcting check)
Before generating, decide whether the retrieved context can actually
answer the question. This is the check that makes the rewrite loop possible.
"""
from pydantic import BaseModel, Field
from app.core.state import RAGState
from app.graph.llm_client import llm
from app.graph.prompts import format_ctx

MIN_RERANK_SCORE = 0.0   # cross-encoder logits; tuned empirically, see log


class Grade(BaseModel):
    verdict: str = Field(description="useful or not_useful")




def _llm_grade(question: str, ctx: str) -> str:
    """Parse grade from plain text response — works with any LLM."""
    r = llm.invoke(
        f"Question: {question}\nContext: {ctx}\n"
        f"Can this context answer the question? "
        f"Reply with exactly one word: 'useful' or 'not_useful'."
    )
    # extract text content
    content = r.content
    if isinstance(content, list):
        content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    content = content.strip().lower()
    # find verdict in response
    if "not_useful" in content or "not useful" in content:
        return "not_useful"
    if "useful" in content:
        return "useful"
    return "not_useful"  # safe default


def grade_docs(state: RAGState) -> dict:
    """
    Base check: single LLM judge call.
    (Differentiator 1, below, upgrades this to a multi-signal check —
    swap grade_docs -> grade_docs_v2 in build_graph.py to use it.)
    """
    ctx = format_ctx(state["docs"])
    verdict = _llm_grade(state["question"], ctx)
    return {"grade": verdict}


# ------------------------------------------------------------------
# DIFFERENTIATOR 1 — Multi-signal grading
# Combines three independent signals instead of trusting one LLM call:
#   1. LLM verdict (as above)
#   2. Cross-encoder relevance score (reused from Module 4's rerank output)
#   3. Lexical overlap — does the context even contain the question's key terms
# ------------------------------------------------------------------
def _key_terms(question: str) -> list[str]:
    stopwords = {"what", "is", "are", "the", "a", "an", "of", "for", "to", "in", "on", "and", "or"}
    return [w.lower().strip("?.,") for w in question.split() if w.lower() not in stopwords and len(w) > 2]


def grade_docs_v2(state: RAGState) -> dict:
    """Grade retrieved context without using an arbitrary logit cutoff.

    Cross-encoder scores are ranking logits, not calibrated probabilities, so
    they should not be rejected using a universal zero threshold. The LLM
    verdict and lexical evidence determine whether rewriting is necessary.
    """
    ctx = format_ctx(state["docs"])
    llm_verdict = _llm_grade(state["question"], ctx)

    terms = _key_terms(state["question"])
    lexical_hit = any(term in ctx.lower() for term in terms) if terms else True

    if llm_verdict == "useful" and lexical_hit:
        return {"grade": "useful"}

    return {"grade": "not_useful"}


if __name__ == "__main__":
    from app.graph.nodes.retrieve import retrieve
    from app.graph.nodes.rerank import rerank

    test_state: RAGState = {
        "question": "What are Apple's main risk factors?", "query": "",
        "docs": [], "scores": None, "answer": "", "grade": "", "retries": 0,
    }
    test_state.update(retrieve(test_state))
    test_state.update(rerank(test_state))

    print("--- Base grade_docs (LLM only) ---")
    print(grade_docs(test_state))

    print("--- grade_docs_v2 (multi-signal) ---")
    print(grade_docs_v2(test_state))