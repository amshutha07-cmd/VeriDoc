"""
Module 3 — Retrieve Node
First real graph node. Pulls candidate chunks from the persisted Chroma
store for the current query, writes them back into state.
"""
from app.core.state import RAGState
from app.ingestion.vector_store import reopen_store
from app.core.config import settings

# Reopened once at import time — reused across every graph run,
# not rebuilt per-request (rebuilding would re-load the embedding client each call).

_store = reopen_store()

_collection_count = _store._collection.count()
if _collection_count == 0:
    print("⚠️  Warning: vector store is empty. Run `python -m app.ingestion.vector_store` first.")



retriever = _store.as_retriever(
    search_type="mmr",   # diversity-aware — avoids 12 near-duplicate chunks
    search_kwargs={
        "k": settings.retrieve_k,
        "fetch_k": settings.retrieve_fetch_k,
    },
)

def retrieve(state: RAGState) -> dict:
    q = state.get("query") or state["question"]
    docs = retriever.invoke(q)
    if not docs:
        print(f"⚠️  No documents retrieved for query: {q!r}")
    return {"docs": docs, "query": q}



if __name__ == "__main__":
    # quick sanity check — always confirm retrieval works before wiring the full graph
    test_state: RAGState = {"question": "What are Apple's main risk factors?", "query": "", 
                             "docs": [], "scores": None, "answer": "", "grade": "", "retries": 0}
    result = retrieve(test_state)
    print(f"Retrieved {len(result['docs'])} docs for query: {result['query']!r}")
    for d in result["docs"][:3]:
        print(f"  [{d.metadata['source']} p{d.metadata['page_label']}] {d.page_content[:100]}")