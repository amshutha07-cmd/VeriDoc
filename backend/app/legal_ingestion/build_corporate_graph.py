from langchain_chroma import Chroma
from app.ingestion.embedder import get_corporate_embeddings
from app.core.config import settings
from app.graph_store.graph_handler import VeriDocGraph
from pathlib import Path

OUTPUT = Path("data/graph_store.json")

REAL_FILINGS = {
    "amazon_2025_annual_report.pdf",
    "aapl-20250927.pdf",
    "apple_fy2023_10k.pdf",
    "apple_fy2024_10k.pdf",
    "microsoft_fy2025_10k.docx",
    "nvidia_fy2025_annual_report.pdf",
}


def main() -> None:
    store = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_corporate_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )
    all_data = store.get(include=["metadatas", "documents"])

    # Group chunks by (source, page) so we don't create duplicate page nodes
    by_source_page = {}
    filing_meta = {}
    for md, doc in zip(all_data["metadatas"], all_data["documents"]):
        source = md.get("source")
        if source not in REAL_FILINGS:
            continue
        page = md.get("page")
        key = (source, page)
        by_source_page.setdefault(key, []).append(doc)
        if source not in filing_meta:
            filing_meta[source] = {
                "organization": md.get("organization", "Unknown"),
                "publication_year": md.get("publication_year"),
                "document_type": md.get("document_type", "filing"),
                "source_url": md.get("source_url", ""),
            }

    graph = VeriDocGraph(storage_path=str(OUTPUT))
    before_nodes = graph.graph.number_of_nodes()
    before_edges = graph.graph.number_of_edges()

    companies_added = set()
    filings_added = set()

    for (source, page), chunks in by_source_page.items():
        meta = filing_meta[source]
        org = meta["organization"]
        year = meta["publication_year"]

        company_id = f"company:{org}"
        if org not in companies_added:
            graph.add_entity(company_id, "Company", {"name": org})
            companies_added.add(org)

        filing_id = f"filing:{source}"
        if source not in filings_added:
            graph.add_entity(filing_id, "Filing", {
                "source": source,
                "organization": org,
                "year": year,
                "document_type": meta["document_type"],
                "source_url": meta["source_url"],
            })
            graph.add_relationship(company_id, filing_id, "FILED", {
                "source": source,
                "year": year,
            })
            filings_added.add(source)

        page_id = f"corp_page:{source}:{page}"
        graph.add_entity(page_id, "Page", {
            "source": source,
            "page": page,
        })
        graph.add_relationship(filing_id, page_id, "HAS_PAGE", {
            "source": source,
            "page": page,
        })

        excerpt = " ".join(chunks)[:900]
        passage_id = f"corp_passage:{source}:{page}"
        graph.add_entity(passage_id, "CorpPassage", {
            "source": source,
            "page": page,
            "excerpt": excerpt,
        })
        graph.add_relationship(page_id, passage_id, "CONTAINS", {
            "source": source,
            "page": page,
        })

    graph.save()
    after_nodes = graph.graph.number_of_nodes()
    after_edges = graph.graph.number_of_edges()
    print(f"GRAPH=OK path={OUTPUT}")
    print(f"before: nodes={before_nodes} edges={before_edges}")
    print(f"after:  nodes={after_nodes} edges={after_edges}")
    print(f"added:  nodes={after_nodes - before_nodes} edges={after_edges - before_edges}")
    print(f"companies={len(companies_added)} filings={len(filings_added)}")


if __name__ == "__main__":
    main()
