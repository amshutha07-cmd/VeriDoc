"""
Module 5 — Grade Node (self-correcting evidence check).

The grader decides whether retrieved context can answer the question before
calling the generation node. It also returns structured evidence metadata for
the frontend.
"""

import re
from typing import Any

from pydantic import BaseModel, Field

from app.core.state import RAGState
from app.graph.llm_client import llm
from app.graph.prompts import format_ctx


# Cross-encoder logits are not calibrated probabilities. This constant is kept
# for compatibility/documentation, but is intentionally not used as a hard
# universal cutoff.
MIN_RERANK_SCORE = 0.0


class Grade(BaseModel):
    verdict: str = Field(description="useful or not_useful")


def _content_to_text(content: Any) -> str:
    """Normalize provider response content into plain text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return " ".join(parts)

    return str(content)


def _llm_grade(question: str, ctx: str) -> str:
    """Ask the LLM for a conservative useful/not_useful verdict."""
    response = llm.invoke(
        f"Question: {question}\n"
        f"Context: {ctx}\n"
        "Can this context answer the question? "
        "Reply with exactly one word: 'useful' or 'not_useful'."
    )

    content = _content_to_text(response.content).strip().lower()

    # Check the negative form first because it contains the word 'useful'.
    if "not_useful" in content or "not useful" in content:
        return "not_useful"
    if "useful" in content:
        return "useful"
    return "not_useful"


def _key_terms(question: str) -> list[str]:
    """Extract simple content terms for a conservative local evidence check."""
    stopwords = {
        "what", "which", "when", "where", "who", "why", "how",
        "is", "are", "was", "were", "the", "a", "an", "of", "for",
        "to", "in", "on", "and", "or", "does", "do", "did", "with",
        "from", "about", "apple", "apples",
    }

    terms = []
    for raw_word in question.lower().split():
        word = raw_word.strip("?.,:;!?()[]{}\"'")
        if len(word) > 2 and word not in stopwords:
            terms.append(word)
    return terms


def _strong_local_evidence(question: str, context: str) -> bool:
    """Return True only when lexical evidence is strong and constraints match."""
    question_lower = question.lower()
    context_lower = context.lower()
    terms = _key_terms(question)

    if not terms:
        return False

    hits = sum(1 for term in terms if term in context_lower)
    lexical_ratio = hits / len(terms)

    # Never bypass the LLM grader when a requested year or number is absent.
    requested_numbers = re.findall(
        r"\b(?:19|20)\d{2}\b|\b\d+(?:\.\d+)?%?\b",
        question_lower,
    )
    if any(not re.search(r"(?<![\w.])" + re.escape(number) + r"(?![\w])", context_lower)
           for number in requested_numbers):
        return False

    return lexical_ratio >= 0.60


def _evidence_metadata(
    state: RAGState,
    status: str,
    confidence: float,
) -> dict:
    """Return focused evidence from reranked chunks.

    Rerank order is already established before this node. We remove only
    navigation/table-of-contents/footer chunks and preserve the remaining
    top chunks so citations from the generator have visible evidence cards.
    """
    documents = list(state.get("docs", []) or [])
    evidence = []

    for document in documents:
        metadata = document.metadata or {}
        text = (document.page_content or "").strip()
        text_lower = text.lower()
        # Exclude a true table-of-contents chunk.
        is_table_of_contents = "table of contents" in text_lower[:400]

        # Exclude a short URL/footer-only chunk, but keep substantive chunks that
        # happen to contain a SEC URL at their end.
        is_short_footer = (
            "https://www.sec.gov/" in text_lower
             and len(text ) < 300
        )

        is_navigation_chunk = is_table_of_contents or is_short_footer

        

        if is_navigation_chunk:
            continue

        evidence.append(
            {
                "source": metadata.get("source", "unknown"),
                "page": metadata.get(
                    "page_label",
                    metadata.get("page"),
                ),
                "excerpt": text[:600],
                "support": "direct",
            }
        )

        if len(evidence) >= 3:
            break

    return {
        "evidence_status": status,
        "evidence_confidence": round(confidence, 3),
        "evidence": evidence,
    }


def grade_docs(state: RAGState) -> dict:
    """Base LLM-only grading node with structured evidence metadata."""
    context = format_ctx(state["docs"])
    verdict = _llm_grade(state["question"], context)

    return {
        "grade": verdict,
        **_evidence_metadata(
            state,
            "supported" if verdict == "useful" else "uncertain",
            0.70 if verdict == "useful" else 0.25,
        ),
    }


def grade_docs_v2(state: RAGState) -> dict:
    """Grade evidence using a fast local gate, then LLM verification if needed.

    The local gate avoids unnecessary remote calls for obviously supported
    questions. Ambiguous questions still use the LLM grader. Questions with
    missing years or numbers are never fast-pathed, preserving safe refusal.
    """
    context = format_ctx(state["docs"])

    # Fast path for clearly supported questions.
    if _strong_local_evidence(state["question"], context):
        return {
            "grade": "useful",
            **_evidence_metadata(state, "supported", 0.85),
        }

    # Ambiguous questions use the LLM grader and may enter the rewrite loop.
    llm_verdict = _llm_grade(state["question"], context)
    terms = _key_terms(state["question"])
    lexical_hit = any(term in context.lower() for term in terms) if terms else True

    if llm_verdict == "useful" and lexical_hit:
        return {
            "grade": "useful",
            **_evidence_metadata(state, "supported", 0.70),
        }

    return {
        "grade": "not_useful",
        **_evidence_metadata(state, "uncertain", 0.25),
    }


if __name__ == "__main__":
    from app.graph.nodes.retrieve import retrieve
    from app.graph.nodes.rerank import rerank

    test_state: RAGState = {
        "question": "What are Apple's main risk factors?",
        "query": "",
        "docs": [],
        "scores": None,
        "answer": "",
        "grade": "",
        "retries": 0,
    }

    test_state.update(retrieve(test_state))
    test_state.update(rerank(test_state))

    print("--- Base grade_docs (LLM only) ---")
    print(grade_docs(test_state))

    print("--- grade_docs_v2 (local gate + LLM) ---")
    print(grade_docs_v2(test_state))
