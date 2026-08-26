"""
Module 6 — Rewrite Node (self-correcting loop)
If grading says the context is weak, rewrite the query and retrieve
again — capped by a retry counter so this can't loop forever.
"""
from app.core.state import RAGState
from app.graph.llm_client import llm


def _extract_text(response) -> str:
    """
    Gemini 3.x can return content as a plain string OR a list of content
    blocks (e.g. [{'type': 'text', 'text': '...'}]). Normalize to a clean string.
    """
    content = response.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [block.get("text", "") for block in content if isinstance(block, dict)]
        return " ".join(p for p in parts if p).strip()
    return str(content).strip()


def rewrite(state: RAGState) -> dict:
    better = llm.invoke(
        "Rewrite the following question into a single, concise search query "
        "optimized for semantic document retrieval. Return ONLY the rewritten "
        f"query, no explanation, no options, no markdown:\n\n{state['question']}"
    )
    clean_query = _extract_text(better)
    return {
        "query": clean_query,
        "retries": state.get("retries", 0) + 1,
    }


if __name__ == "__main__":
    test_state: RAGState = {
        "question": "What are Apple's main risk factors?", "query": "",
        "docs": [], "scores": None, "answer": "", "grade": "not_useful", "retries": 0,
    }
    result = rewrite(test_state)
    print("Rewritten query:", repr(result["query"]))
    print("Retries now:", result["retries"])