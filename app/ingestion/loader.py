"""
Module 1a — Load & Scrape
Turns raw files into LangChain Document objects with clean metadata.
Supports PDF (primary), with TXT/Markdown as easy extensions.
"""
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    PyPDFDirectoryLoader,
    TextLoader,
)


def load_single_pdf(path: str) -> List[Document]:
    """Load one PDF file. Each page becomes a separate Document."""
    docs = PyPDFLoader(path).load()
    return _tag_source(docs)


def load_pdf_directory(dir_path: str) -> List[Document]:
    """Load every PDF in a folder."""
    docs = PyPDFDirectoryLoader(dir_path).load()
    return _tag_source(docs)


def load_text_file(path: str) -> List[Document]:
    """Load a .txt or .md file (extension beyond the original tutorial scope)."""
    docs = TextLoader(path, encoding="utf-8").load()
    return _tag_source(docs)


def load_any(path: str) -> List[Document]:
    """Dispatch by file extension. Point this at a single file or a folder."""
    p = Path(path)
    if p.is_dir():
        return load_pdf_directory(str(p))
    if p.suffix.lower() == ".pdf":
        return load_single_pdf(str(p))
    if p.suffix.lower() in (".txt", ".md"):
        return load_text_file(str(p))
    raise ValueError(f"Unsupported file type: {p.suffix}")


def _tag_source(docs: List[Document]) -> List[Document]:
    """
    Ensure every doc has a clean 'source' and 'page' in metadata.
    This is what makes citations possible downstream in the prompt step.
    """
    for d in docs:
        d.metadata["source"] = Path(d.metadata.get("source", "unknown")).name
        d.metadata.setdefault("page", 0)
    return docs


if __name__ == "__main__":
    # quick sanity check — always print a sample before trusting the pipeline
    from app.core.config import settings
    docs = load_pdf_directory(settings.data_dir)
    print(f"Loaded {len(docs)} pages")
    if docs:
        print(docs[0].metadata)
        print(docs[0].page_content[:200])