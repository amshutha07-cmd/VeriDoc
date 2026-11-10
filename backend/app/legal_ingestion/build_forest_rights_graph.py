import json
from pathlib import Path
from app.graph_store.graph_handler import VeriDocGraph

INPUT = Path("data/legal_corpus/chunks/acts-pages.jsonl")
OUTPUT = Path("data/graph_store.json")
TARGET = "2007-02.pdf"

# Sections appearing on each printed page of this supplied Act PDF.
SECTION_PAGES = {
    1: [],
    2: [1, 2],
    3: [2],
    4: [3],
    5: [4],
    6: [5],
    7: [6],
    8: [7, 8, 9, 10],
    9: [10, 11, 12, 13, 14],
}


def excerpt_for(text: str, section: int) -> str:
    """Prefer text near the section marker; otherwise retain the page text."""
    marker = f"{section}."
    position = text.find(marker)
    if position >= 0:
        return text[position:position + 900]
    return text[:900]


def main() -> None:
    rows = [
        json.loads(line)
        for line in INPUT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = [row for row in rows if row["filename"] == TARGET]
    if not rows:
        raise RuntimeError(f"No rows found for {TARGET}")

    if OUTPUT.exists():
        OUTPUT.unlink()

    graph = VeriDocGraph(storage_path=str(OUTPUT))
    act_id = f"act:{TARGET}"
    graph.add_entity(act_id, "Act", {
        "source": TARGET,
        "title": "Scheduled Tribes and Other Traditional Forest Dwellers (Recognition of Forest Rights) Act, 2006",
    })

    for row in sorted(rows, key=lambda item: int(item["page_number"])):
        page = int(row["page_number"])
        text = row.get("text", "")
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

        for section in SECTION_PAGES.get(page, []):
            section_id = f"section:{TARGET}:{section}"
            graph.add_entity(section_id, "Section", {
                "source": TARGET,
                "section": str(section),
            })
            graph.add_relationship(act_id, section_id, "HAS_SECTION", {
                "source": TARGET,
                "section": str(section),
            })
            graph.add_relationship(section_id, page_id, "LOCATED_ON", {
                "source": TARGET,
                "page": page,
            })

            passage_id = f"passage:{TARGET}:{page}:section-{section}"
            graph.add_entity(passage_id, "SourcePassage", {
                "source": TARGET,
                "page": page,
                "section": str(section),
                "excerpt": excerpt_for(text, section),
                "sha256": row.get("sha256", ""),
            })
            graph.add_relationship(page_id, passage_id, "CONTAINS", {
                "source": TARGET,
                "page": page,
                "section": str(section),
            })

    graph.save()
    print(f"GRAPH=OK path={OUTPUT} nodes={graph.graph.number_of_nodes()} edges={graph.graph.number_of_edges()}")


if __name__ == "__main__":
    main()
