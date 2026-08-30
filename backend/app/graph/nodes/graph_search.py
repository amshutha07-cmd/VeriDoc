from typing import Any
from app.graph_store.graph_handler import VeriDocGraph


def graph_search(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("domain") != "indian_law":
        return {"graph_results": []}

    graph = VeriDocGraph(storage_path="data/graph_store.pkl")
    keywords = []
    for entity in state.get("entities", []):
        text = str(entity.get("text", "")).strip()
        if not text:
            continue
        if ":" in text:
            text = text.split(":", 1)[1].strip()
        text = text.rstrip(".").lower()
        if text and text != "none":
            keywords.append(text)
    if not keywords:
        return {"graph_results": []}

    results = []
    seen = set()
    for node_id, data in graph.graph.nodes(data=True):
        if data.get("type") != "SourcePassage":
            continue
        haystack = str(data.get("excerpt", "")).lower()
        if not any(keyword in haystack for keyword in keywords):
            continue

        key = (data.get("source"), data.get("page"), data.get("section"))
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "node": node_id,
            "type": "SourcePassage",
            "source": data.get("source", "2007-02.pdf"),
            "page": data.get("page"),
            "section": data.get("section"),
            "excerpt": data.get("excerpt", ""),
            "relationship": "Act → Section → Page → Passage",
        })

    results.sort(key=lambda item: (item["page"] or 0, str(item["section"])))
    return {"graph_results": results[:10]}
