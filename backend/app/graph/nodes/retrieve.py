"""Domain-aware hybrid retrieval for corporate and Indian-law corpora."""
from langchain_core.documents import Document
from langchain_chroma import Chroma
from app.core.state import RAGState
from app.core.config import settings
from app.graph.source_filter import filter_legal_sources
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


def _graph_documents(state: RAGState, domain_label: str) -> list[Document]:
    documents = []
    for item in state.get("graph_results", []):
        excerpt = str(item.get("excerpt", "")).strip()
        if not excerpt:
            continue
        documents.append(Document(
            page_content=excerpt,
            metadata={
                "domain": domain_label,
                "source": item.get("source", ""),
                "filename": item.get("source", ""),
                "page": item.get("page"),
                "page_number": item.get("page"),
                "section_reference": item.get("section", ""),
                "document_type": "Act" if domain_label == "indian_law" else "Filing",
                "retrieval_mode": "graph",
            },
        ))
    return documents


def _merge_with_graph(state: RAGState, query: str, vector_docs: list[Document], domain_label: str) -> dict:
    graph_docs = _graph_documents(state, domain_label)
    graph_sources = {
        doc.metadata.get("source")
        for doc in graph_docs
        if doc.metadata.get("source")
    }
    # When graph evidence exists, restrict vector evidence to the same source(s).
    if graph_sources:
        vector_docs = [
            doc for doc in vector_docs
            if doc.metadata.get("source", doc.metadata.get("filename", "")) in graph_sources
        ]
    merged = []
    seen = set()
    for doc in graph_docs + vector_docs:
        source = doc.metadata.get("source", doc.metadata.get("filename", ""))
        page = doc.metadata.get("page", doc.metadata.get("page_number"))
        section = doc.metadata.get("section_reference", "")
        key = (source, page, section, doc.page_content[:120])
        if key in seen:
            continue
        seen.add(key)
        doc.metadata["page"] = int(page) if page is not None else 1
        doc.metadata["page_label"] = str(doc.metadata["page"])
        doc.metadata["source"] = source
        merged.append(doc)
    print(f"retrieval_domain={domain_label} graph_docs={len(graph_docs)} vector_docs={len(vector_docs)} merged={len(merged)}")
    return {"docs": merged, "query": query}


def retrieve(state: RAGState) -> dict:
    query = state.get("query") or state["question"]
    is_legal = state.get("domain") == "indian_law"
    retriever = _legal_retriever if is_legal else _corporate_retriever
    vector_docs = retriever.invoke(query)

    if is_legal:
        vector_docs = filter_legal_sources(query, vector_docs)
        return _merge_with_graph(state, query, vector_docs, "indian_law")

    # Corporate: apply the same graph-restricts-vector pattern as legal, when graph
    # evidence exists (i.e. entity extraction successfully identified a company/year).
    return _merge_with_graph(state, query, vector_docs, "corporate")


if __name__ == "__main__":
    pass
