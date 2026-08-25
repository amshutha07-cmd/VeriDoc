"""Recursive metadata-aware loader for PDF and DOCX corpus files."""

from pathlib import Path
from typing import List
import re

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from docx import Document as WordDocument


SOURCE_URLS = {
    "aapl-20250927.pdf": "https://investor.apple.com/investor-relations/default.aspx",
    "apple_fy2023_10k.pdf": "https://investor.apple.com/investor-relations/default.aspx",
    "apple_fy2024_10k.pdf": "https://investor.apple.com/investor-relations/default.aspx",
    "apple_fy2022_10k.pdf": "https://investor.apple.com/investor-relations/default.aspx",
    "microsoft_fy2025_10k.docx": "https://www.microsoft.com/investor/reports/ar25/download-center/index.html",
    "nvidia_fy2025_annual_report.pdf": "https://investor.nvidia.com/financial-info/annual-reports-and-proxies/default.aspx",
    "amazon_2025_annual_report.pdf": "https://ir.aboutamazon.com/annual-reports-proxies-and-shareholder-letters/default.aspx",
    "world_bank_group_annual_report_2025.pdf": "https://www.worldbank.org/en/about/annual-report/world-bank-group-downloads",
}


def _infer_metadata(path: Path, root: Path ) -> dict:
    filename = path.name
    lower_name = filename.lower()
    relative_parts = [part.lower() for part in path.relative_to(root).parts]

    if "corporate_filings" in relative_parts:
        category = "corporate_filing"
        document_type = "annual_report"
    elif "regulation" in relative_parts:
        category = "banking_regulation"
        document_type = "regulatory_document"
    elif "macro_reports" in relative_parts:
        category = "macroeconomics"
        document_type = "institutional_report"
    elif "education" in relative_parts:
        category = "education"
        document_type = "textbook"
    else:
        category = "general_finance"
        document_type = "financial_document"

    if "apple" in lower_name or "aapl" in lower_name:
        organization, country = "Apple", "United States"
    elif "microsoft" in lower_name or "msft" in lower_name:
        organization, country = "Microsoft", "United States"
    elif "nvidia" in lower_name or "nvda" in lower_name:
        organization, country = "NVIDIA", "United States"
    elif "amazon" in lower_name or "amzn" in lower_name:
        organization, country = "Amazon", "United States"
    elif any(term in lower_name for term in ("reserve", "rbi", "notification")):
        organization, country = "Reserve Bank of India", "India"
    elif "world_bank" in lower_name:
        organization, country = "World Bank Group", "Global"
    elif "imf" in lower_name:
        organization, country = "International Monetary Fund", "Global"
    elif "economics" in lower_name or "accounting" in lower_name:
        organization, country = "Open educational resource", "Global"
    elif "business" in lower_name or "data-science" in lower_name or "information_systems" in lower_name:
        organization, country = "Open educational resource", "Global"
    else:
        organization, country = "Unknown", "Unknown"

    if category == "general_finance" and organization in {"Apple", "Microsoft", "NVIDIA", "Amazon"}:
        category = "corporate_filing"
        document_type = "annual_report"

    year_match = re.search(r"(?:19|20)\d{2}", filename)
    year = int(year_match.group(0)) if year_match else None

    return {
        "organization": organization,
        "country": country,
        "category": category,
        "document_type": document_type,
        "publication_year": year,
        "source_url": SOURCE_URLS.get(filename, ""),
        "source": filename,
        "file_path": str(path),
    }


def _tag_source(docs: List[Document], path: Path, root: Path) -> List[Document]:
    base_metadata = _infer_metadata(path, root)

    for document in docs:
        document.metadata.update(base_metadata)
        raw_page = document.metadata.get("page")
        try:
            page_number = int(raw_page) + 1 if raw_page is not None else 1
        except (TypeError, ValueError):
            page_number = 1
        document.metadata["page"] = page_number
        document.metadata["page_label"] = str(page_number)

    return docs


def load_single_pdf(path: str, root: str | None = None) -> List[Document]:
    file_path = Path(path).resolve()
    root_path = Path(root).resolve() if root else file_path.parent
    docs = PyPDFLoader(str(file_path)).load()
    return _tag_source(docs, file_path, root_path)


def load_single_docx(path: str, root: str | None = None) -> List[Document]:
    file_path = Path(path).resolve()
    root_path = Path(root).resolve() if root else file_path.parent
    word_document = WordDocument(str(file_path))
    paragraphs = [p.text.strip() for p in word_document.paragraphs if p.text.strip()]
    tables = []
    for table in word_document.tables:
        for row in table.rows:
            tables.append(" | ".join(cell.text.strip() for cell in row.cells))
    text = "\n".join(paragraphs + tables)
    docs = [Document(page_content=text, metadata={})]
    return _tag_source(docs, file_path, root_path)


def load_pdf_directory(dir_path: str) -> List[Document]:
    """Recursively load PDFs and DOCX files under the corpus root."""
    root = Path(dir_path).resolve()
    all_docs: List[Document] = []
    paths = sorted([*root.rglob("*.pdf"), *root.rglob("*.docx")])

    for path in paths:
        try:
            if path.suffix.lower() == ".docx":
                docs = load_single_docx(str(path), str(root))
            else:
                docs = load_single_pdf(str(path), str(root))
            all_docs.extend(docs)
            print(f"Loaded {path.relative_to(root)}: {len(docs)} document(s)")
        except Exception as exc:
            print(f"WARNING: skipped {path.name}: {exc}")

    return all_docs


def load_text_file(path: str, root: str | None = None) -> List[Document]:
    file_path = Path(path).resolve()
    root_path = Path(root).resolve() if root else file_path.parent
    docs = TextLoader(str(file_path), encoding="utf-8").load()
    return _tag_source(docs, file_path, root_path)


def load_any(path: str) -> List[Document]:
    target = Path(path)
    if target.is_dir():
        return load_pdf_directory(str(target))
    if target.suffix.lower() == ".pdf":
        return load_single_pdf(str(target))
    if target.suffix.lower() == ".docx":
        return load_single_docx(str(target))
    if target.suffix.lower() in (".txt", ".md"):
        return load_text_file(str(target))
    raise ValueError(f"Unsupported file type: {target.suffix}")


if __name__ == "__main__":
    from app.core.config import settings
    documents = load_pdf_directory(settings.data_dir)
    print(f"TOTAL DOCUMENTS LOADED: {len(documents)}")
    if documents:
        print("SAMPLE METADATA:")
        print(documents[0].metadata)
        print("SAMPLE TEXT:")
        print(documents[0].page_content[:300])
