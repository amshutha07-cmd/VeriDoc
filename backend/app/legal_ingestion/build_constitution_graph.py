import json
from pathlib import Path
from app.graph_store.graph_handler import VeriDocGraph

INPUT = Path("data/legal_corpus/chunks/acts-pages.jsonl")
OUTPUT = Path("data/graph_store.json")
TARGET = "doc3.pdf"
ARTICLE_PAGES_FILE = Path(__file__).parent / "article_pages_doc3.json"


def excerpt_for(text: str, article: str) -> str:
    marker = f"{article}."
    position = text.find(marker)
    if position >= 0:
        return text[position:position + 900]
    return text[:900]


def main() -> None:
    article_pages = json.loads(ARTICLE_PAGES_FILE.read_text(encoding="utf-8"))

    rows = [json.loads(l) for l in INPUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r["filename"] == TARGET]
    if not rows:
        raise RuntimeError(f"No rows found for {TARGET}")
    rows_by_page = {int(r["page_number"]): r for r in rows}

    # Additive - existing Forest Rights + Motor Vehicles Act graph stays intact
    graph = VeriDocGraph(storage_path=str(OUTPUT))
    before_nodes = graph.graph.number_of_nodes()
    before_edges = graph.graph.number_of_edges()

    act_id = f"act:{TARGET}"
    graph.add_entity(act_id, "Act", {
        "source": TARGET,
        "title": "The Constitution of India",
    })

    pages_added = set()
    for article, pages in article_pages.items():
        for page in pages:
            row = rows_by_page.get(page)
            if not row:
                continue
            text = row.get("text", "")

            if page not in pages_added:
                page_id = f"page:{TARGET}:{page}"
                graph.add_entity(page_id, "Page", {
                    "source": TARGET,
                    "page": page,
                    "sha256": row.get("sha256", ""),
                    "retrieved_at": row.get("retrieved_at", ""),
                })
                graph.add_relationship(act_id, page_id, "HAS_PAGE", {
                    "source": TARGET,
                    "page": page,
                })
                pages_added.add(page)

            page_id = f"page:{TARGET}:{page}"
            article_id = f"article:{TARGET}:{article}"
            graph.add_entity(article_id, "Article", {
                "source": TARGET,
                "article": article,
            })
            graph.add_relationship(act_id, article_id, "HAS_ARTICLE", {
                "source": TARGET,
                "article": article,
            })
            graph.add_relationship(article_id, page_id, "LOCATED_ON", {
                "source": TARGET,
                "page": page,
            })

            passage_id = f"passage:{TARGET}:{page}:article-{article}"
            graph.add_entity(passage_id, "SourcePassage", {
                "source": TARGET,
                "page": page,
                "article": article,
                "excerpt": excerpt_for(text, article),
                "sha256": row.get("sha256", ""),
            })
            graph.add_relationship(page_id, passage_id, "CONTAINS", {
                "source": TARGET,
                "page": page,
                "article": article,
            })

    graph.save()
    after_nodes = graph.graph.number_of_nodes()
    after_edges = graph.graph.number_of_edges()
    print(f"GRAPH=OK path={OUTPUT}")
    print(f"before: nodes={before_nodes} edges={before_edges}")
    print(f"after:  nodes={after_nodes} edges={after_edges}")
    print(f"added:  nodes={after_nodes - before_nodes} edges={after_edges - before_edges}")


if __name__ == "__main__":
    main()
