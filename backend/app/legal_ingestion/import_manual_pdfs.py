from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
from pypdf import PdfReader

MANIFEST = Path("backend/data/legal_corpus/manifests/acts-manifest.jsonl")
OUT = Path("backend/data/legal_corpus/chunks/acts-pages.jsonl")


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    # Repair common UTF-8 decoded as Latin-1/Windows-1252 when reversible.
    if any(marker in text for marker in ("Ã", "Â", "â", "à¤")):
        try:
            repaired = text.encode("latin1").decode("utf-8")
            if repaired.count("�") <= text.count("�"):
                text = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return re.sub(r"\s+", " ", text).strip()


def section_reference(text: str) -> str | None:
    match = re.search(r"\b(?:Section|SECTION|Sec\.?|Rule|RULE)\s+[0-9A-Za-zA-Z()/-]+", text)
    return match.group(0) if match else None

records = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
rows = []

for record in records:
    pdf_path = Path(record["path"])
    pdf_bytes = pdf_path.read_bytes()
    actual_hash = hashlib.sha256(pdf_bytes).hexdigest()
    if actual_hash != record["sha256"]:
        raise RuntimeError(f"Hash changed: {pdf_path.name}")

    reader = PdfReader(str(pdf_path))
    for page_number, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        if not text:
            continue
        rows.append({
            "filename": record["filename"],
            "document_type": "Act",
            "source_type": "manual_import",
            "page_number": page_number,
            "sha256": record["sha256"],
            "section_reference": section_reference(text),
            "retrieved_at": record["retrieved_at"],
            "text": text,
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8", newline="\n") as handle:
    for row in rows:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"imported_pages={len(rows)}")
print(f"output={OUT}")
