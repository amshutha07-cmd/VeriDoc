# """
# Module 1d â€” Store
# Persists embedded chunks in Chroma so ingestion runs once, not on every
# app start. Also exposes a reopen() to load an already-built index.
# """
# from typing import List
# from langchain_core.documents import Document
# from langchain_chroma import Chroma
# from app.core.config import settings
# from app.ingestion.embedder import get_corporate_embeddings


# def build_store(chunks: List[Document]) -> Chroma:
#     """First-time build: embeds chunks and writes them to disk."""
#     embeddings = get_corporate_embeddings()
#     store = Chroma.from_documents(
#         documents=chunks,
#         embedding=embeddings,
#         collection_name=settings.chroma_collection_name,
#         persist_directory=settings.chroma_persist_dir,
#     )
#     return store


# def reopen_store() -> Chroma:
#     """Later runs: reopen the persisted index without re-embedding."""
#     embeddings = get_corporate_embeddings()
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
Module 1d â€” Store
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
from app.ingestion.embedder import get_corporate_embeddings

BATCH_SIZE = 20          # chunks per request batch
DELAY_SECONDS = 0       # pause between batches, stays safely under 100/min


def build_store(chunks: List[Document]) -> Chroma:
    """First-time build: embeds chunks in rate-limited batches, writes to disk."""
    embeddings = get_corporate_embeddings()
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
    embeddings = get_corporate_embeddings()
    store = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
    return store


if __name__ == "__main__":
    from app.ingestion.loader import load_pdf_directory
    from app.ingestion.chunker import chunk_documents
    from app.ingestion.graph_ingestor import ingest_to_graph # New logic
    import os

    # 1. Force the correct path
    data_path = os.path.join(os.getcwd(), "backend", "data")
    print(f"Searching for PDFs in: {data_path}")

    # 2. Load and Chunk
    documents = load_pdf_directory(data_path)
    if not documents:
        print("❌ Error: No documents found. Check if PDFs are in backend/data/")
    else:
        chunks = chunk_documents(documents)

        # 3. Populate Vector Store (ChromaDB)
                # 3. Populate Vector Store (ChromaDB) - Batched for scale
        store = reopen_store()

        # Split chunks into groups of 500 to stay under Chroma's 5461 limit
        batch_size = 500
        total_chunks = len(chunks)
        print(f"Total chunks to index: {total_chunks}")

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]
            store.add_documents(batch)
            print(f"✅ Indexed batch {i//batch_size + 1} (Chunks {i} to {min(i + batch_size, total_chunks)})")

        print(f"✅ Successfully indexed all {total_chunks} chunks.")

