"""Domain-aware retrieval for corporate and Indian-law corpora."""

from app.core.state import RAGState
from app.core.config import settings
from app.ingestion.vector_store import reopen_store
from app.ingestion.embedder import get_embeddings
from langchain_chroma import Chroma

LEGAL_COLLECTION = "veridoc_legal"

# Corporate collection: existing behavior is preserved.
_corporate_store = reopen_store()
_corporate_retriever = _corporate_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": settings.retrieve_k,
        "fetch_k": settings.retrieve_fetch_k,
    },
)

# Legal collection: isolated from corporate documents.
_legal_store = Chroma(
    collection_name=LEGAL_COLLECTION,
    embedding_function=get_embeddings(),
    persist_directory=settings.chroma_persist_dir,
)

if _legal_store._collection.count() == 0:
    raise RuntimeError("veridoc_legal is empty; run the legal indexer first")

_legal_retriever = _legal_store.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": settings.retrieve_k,
        "fetch_k": settings.retrieve_fetch_k,
    },
)


def retrieve(state: RAGState) -> dict:
    query = state.get("query") or state["question"]
    is_legal = state.get("domain") == "indian_law"
    retriever = _legal_retriever if is_legal else _corporate_retriever
    docs = retriever.invoke(query)

    if not docs:
        print(f"No documents retrieved for query: {query!r}")

    print(
        f"retrieval_domain={'indian_law' if is_legal else 'corporate'} "
        f"docs={len(docs)}"
    )
    return {"docs": docs, "query": query}
