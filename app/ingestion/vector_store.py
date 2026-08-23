# """
# Module 1d — Store
# Persists embedded chunks in Chroma so ingestion runs once, not on every
# app start. Also exposes a reopen() to load an already-built index.
# """
# from typing import List
# from langchain_core.documents import Document
# from langchain_chroma import Chroma
# from app.core.config import settings
# from app.ingestion.embedder import get_embeddings


# def build_store(chunks: List[Document]) -> Chroma:
#     """First-time build: embeds chunks and writes them to disk."""
#     embeddings = get_embeddings()
#     store = Chroma.from_documents(
#         documents=chunks,
#         embedding=embeddings,
#         collection_name=settings.chroma_collection_name,
#         persist_directory=settings.chroma_persist_dir,
#     )
#     return store


# def reopen_store() -> Chroma:
#     """Later runs: reopen the persisted index without re-embedding."""
#     embeddings = get_embeddings()
#     store = Chroma(
#         collection_name=settings.chroma_collection_name,
#         embedding_function=embeddings,
#         persist_directory=settings.chroma_persist_dir,
#     )
#     return store


# if __name__ == "__main__":
#     from app.ingestion.loader import load_pdf_directory
#     from app.ingestion.chunker import chunk_documents

#     docs = load_pdf_directory(settings.data_dir)
#     chunks = chunk_documents(docs)
#     store = build_store(chunks)
#     print(f"Indexed {len(chunks)} chunks into '{settings.chroma_collection_name}'")
"""
Module 1d — Store
Persists embedded chunks in Chroma so ingestion runs once, not on every
app start. Also exposes a reopen() to load an already-built index.

Embeds in small batches with a delay to respect Gemini free-tier rate
limits (100 requests/minute on embed_content).
"""
import time
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from app.core.config import settings
from app.ingestion.embedder import get_embeddings

BATCH_SIZE = 20          # chunks per request batch
DELAY_SECONDS = 15       # pause between batches, stays safely under 100/min


def build_store(chunks: List[Document]) -> Chroma:
    """First-time build: embeds chunks in rate-limited batches, writes to disk."""
    embeddings = get_embeddings()
    store = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )

    total = len(chunks)
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        store.add_documents(batch)
        done = min(i + BATCH_SIZE, total)
        print(f"Embedded {done}/{total} chunks")
        if done < total:
            time.sleep(DELAY_SECONDS)

    return store


def reopen_store() -> Chroma:
    """Later runs: reopen the persisted index without re-embedding."""
    embeddings = get_embeddings()
    store = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
    return store


if __name__ == "__main__":
    from app.ingestion.loader import load_pdf_directory
    from app.ingestion.chunker import chunk_documents

    docs = load_pdf_directory(settings.data_dir)
    chunks = chunk_documents(docs)
    print(f"Loaded {len(docs)} pages -> {len(chunks)} chunks. Starting batched embed...")
    store = build_store(chunks)
    print(f"Indexed {len(chunks)} chunks into '{settings.chroma_collection_name}'")