"""
POST /ingest — upload PDFs, run the full ingestion pipeline.
"""
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from app.core.config import settings
from app.ingestion.loader import load_pdf_directory
from app.ingestion.chunker import chunk_documents
from app.ingestion.vector_store import build_store

router = APIRouter()


@router.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(exist_ok=True, parents=True)

    for f in files:
        dest = data_dir / f.filename
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)

    docs = load_pdf_directory(str(data_dir))
    chunks = chunk_documents(docs)
    build_store(chunks)

    return {"pages": len(docs), "chunks": len(chunks)}


@router.get("/ingest/stats")
async def ingest_stats():
    from app.ingestion.vector_store import reopen_store
    store = reopen_store()
    return {"chunk_count": store._collection.count()}