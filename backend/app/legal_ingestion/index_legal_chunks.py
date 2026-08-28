from pathlib import Path
import json

from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.core.config import settings
from app.ingestion.embedder import get_embeddings

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "legal_corpus" / "chunks" / "acts-pages.jsonl"
LEGAL_COLLECTION = "veridoc_legal"
BATCH_SIZE = 100


def main() -> None:
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing legal chunks: {INPUT}")

    rows = [
        json.loads(line)
        for line in INPUT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise RuntimeError("No legal chunks found")

    embeddings = get_embeddings()
    store = Chroma(
        collection_name=LEGAL_COLLECTION,
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )

    existing = store._collection.count()
    if existing:
        print(f"SKIP: {LEGAL_COLLECTION} already contains {existing} chunks")
        return

    documents = []
    for row in rows:
        filename = row["filename"]
        if filename in {"doc1.pdf", "doc3.pdf"}:
            document_type = "Constitution"
        else:
            document_type = "Act"

        metadata = {
            "domain": "indian_law",
            "document_type": document_type,
            "source": filename,
            "filename": filename,
            "page_number": int(row["page_number"]),
            "sha256": row["sha256"],
            "section_reference": row.get("section_reference") or "",
            "source_type": row.get("source_type", "manual_import"),
            "retrieved_at": row.get("retrieved_at", ""),
        }
        documents.append(Document(page_content=row["text"], metadata=metadata))

    for start in range(0, len(documents), BATCH_SIZE):
        batch = documents[start : start + BATCH_SIZE]
        store.add_documents(batch)
        print(f"indexed={min(start + len(batch), len(documents))}/{len(documents)}")

    print(f"LEGAL_INDEX=OK collection={LEGAL_COLLECTION} chunks={store._collection.count()}")


if __name__ == "__main__":
    main()
