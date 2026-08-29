"""Upload and incrementally index documents into the correct collection."""
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from langchain_chroma import Chroma
from app.core.config import settings
from app.ingestion.loader import load_any
from app.ingestion.chunker import chunk_documents
from app.ingestion.embedder import get_embeddings, get_corporate_embeddings

router = APIRouter()
LEGAL_COLLECTION = "veridoc_legal"


def _store_for(domain: str) -> Chroma:
    if domain == "legal":
        return Chroma(
            collection_name=LEGAL_COLLECTION,
            embedding_function=get_embeddings(),
            persist_directory=settings.chroma_persist_dir,
        )
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_corporate_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


@router.post("/ingest")
async def ingest(
    files: list[UploadFile] = File(...),
    domain: str = Form("legal"),
):
    domain = domain.lower().strip()
    if domain not in {"legal", "corporate"}:
        raise HTTPException(status_code=400, detail="domain must be legal or corporate")

    data_dir = Path(settings.data_dir) / "uploads" / domain
    data_dir.mkdir(exist_ok=True, parents=True)
    uploaded_docs = []
    saved_files = []

    for upload in files:
        safe_name = Path(upload.filename or "upload.bin").name
        if Path(safe_name).suffix.lower() not in {".pdf", ".docx"}:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {safe_name}")
        destination = data_dir / safe_name
        with destination.open("wb") as output:
            shutil.copyfileobj(upload.file, output)
        uploaded_docs.extend(load_any(str(destination)))
        saved_files.append(safe_name)

    chunks = chunk_documents(uploaded_docs)
    if chunks:
        _store_for(domain).add_documents(chunks)

    store = _store_for(domain)
    return {
        "files": saved_files,
        "domain": domain,
        "pages": len(uploaded_docs),
        "chunks": len(chunks),
        "collection": LEGAL_COLLECTION if domain == "legal" else settings.chroma_collection_name,
        "total_chunks": store._collection.count(),
        "status": "ready",
    }


@router.get("/ingest/stats")
async def ingest_stats():
    handbook = _store_for("corporate")
    legal = _store_for("legal")
    return {
        "handbook_chunks": handbook._collection.count(),
        "legal_chunks": legal._collection.count(),
    }
