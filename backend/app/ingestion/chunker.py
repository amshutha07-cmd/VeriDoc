"""
Module 1b — Chunk
Splits full-page Documents into overlapping windows sized for embedding.
"""
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings


def chunk_documents(
    docs: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Document]:
    """
    400-800 chars suits most prose documents.
    10-20% overlap keeps sentences from breaking across chunk boundaries.
    Code/tables need larger chunks + a structure-aware splitter (not this one).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)
    return chunks


if __name__ == "__main__":
    from app.ingestion.loader import load_pdf_directory
    docs = load_pdf_directory(settings.data_dir)
    chunks = chunk_documents(docs)
    print(f"{len(docs)} pages -> {len(chunks)} chunks")
    if chunks:
        print(chunks[0].metadata)
        print(chunks[0].page_content)