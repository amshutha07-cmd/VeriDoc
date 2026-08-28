from pathlib import Path


def test_selected_legal_pdfs_are_ignored():
    root = Path("backend/data/legal_corpus/acts/incoming")
    names = {"A1988-59.pdf", "2007-02.pdf", "doc1.pdf", "doc3.pdf"}
    present = {p.name for p in root.glob("*.pdf")}
    assert present.issubset(names)


def test_legal_ingestion_modules_exist():
    assert Path("backend/app/legal_ingestion/collect_legislation.py").exists()
    assert Path("backend/app/legal_ingestion/discover_official_links.py").exists()
