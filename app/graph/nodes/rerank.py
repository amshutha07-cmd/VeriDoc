"""
Module 4 — Rerank Node (precision layer)
Embedding search is approximate; a cross-encoder reads question+chunk
together for true relevance, then we keep only the sharpest few.
"""
from sentence_transformers import CrossEncoder
from app.core.state import RAGState
from app.core.config import settings

# Loaded once at import time — loading the cross-encoder model has real
# startup cost, shouldn't happen per-request.
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(state: RAGState) -> dict:
    docs = state["docs"]
    if not docs:
        return {"docs": [], "scores": []}

    pairs = [(state["query"], d.page_content) for d in docs]
    raw_scores = reranker.predict(pairs)

    ranked = sorted(zip(raw_scores, docs), key=lambda x: -x[0])
    top = ranked[: settings.rerank_top_n]

    return {
        "docs": [d for _, d in top],
        "scores": [float(s) for s, _ in top],   # populates RAGState.scores — used by Grade next
    }


if __name__ == "__main__":
    from app.graph.nodes.retrieve import retrieve

    test_state: RAGState = {
        "question": "What are Apple's main risk factors?", "query": "",
        "docs": [], "scores": None, "answer": "", "grade": "", "retries": 0,
    }
    retrieved = retrieve(test_state)
    test_state.update(retrieved)

    result = rerank(test_state)
    print(f"Reranked {len(retrieved['docs'])} -> kept top {len(result['docs'])}")
    for score, doc in zip(result["scores"], result["docs"]):
        print(f"  score={score:.3f}  [{doc.metadata['source']} p{doc.metadata['page_label']}] {doc.page_content[:80]}")