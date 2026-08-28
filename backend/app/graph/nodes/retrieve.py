"""Domain-aware retrieval for corporate and Indian-law corpora."""
from app.core.state import RAGState
from app.core.config import settings
from langchain_chroma import Chroma
from app.ingestion.vector_store import reopen_store
from app.ingestion.embedder import get_embeddings, get_corporate_embeddings

LEGAL_COLLECTION = "veridoc_legal"

_corporate_store = Chroma(
    collection_name=settings.chroma_collection_name,
    embedding_function=get_corporate_embeddings(),
    persist_directory=settings.chroma_persist_dir,
)
_corporate_retriever = _corporate_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": settings.retrieve_k, "fetch_k": settings.retrieve_fetch_k},
)

_legal_store = Chroma(
    collection_name=LEGAL_COLLECTION,
    embedding_function=get_embeddings(),
    persist_directory=settings.chroma_persist_dir,
)
if _legal_store._collection.count() == 0:
    raise RuntimeError("veridoc_legal is empty; run the legal indexer first")

_legal_retriever = _legal_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": settings.retrieve_k, "fetch_k": settings.retrieve_fetch_k},
)


def retrieve(state: RAGState) -> dict:
    query = state.get("query") or state["question"]
    is_legal = state.get("domain") == "indian_law"
    retriever = _legal_retriever if is_legal else _corporate_retriever
    docs = retriever.invoke(query)

    if is_legal:
        for doc in docs:
            page_number = doc.metadata.get("page_number", doc.metadata.get("page", 1))
            doc.metadata["page"] = int(page_number)
            doc.metadata["page_label"] = str(page_number)
            doc.metadata["source"] = doc.metadata.get("filename", doc.metadata.get("source", ""))

    print(f"retrieval_domain={'indian_law' if is_legal else 'corporate'} docs={len(docs)}")
    return {"docs": docs, "query": query}
