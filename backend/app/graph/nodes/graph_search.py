from typing import Any
import re
from app.graph_store.graph_handler import VeriDocGraph

MIN_KEYWORD_LENGTH = 4

ACT_SOURCE_MAP = {
    "forest rights act": ["2007-02.pdf"],
    "motor vehicles act": ["A1988-59.pdf"],
    "constitution of india": ["doc1.pdf", "doc3.pdf"],
    "constitution": ["doc1.pdf", "doc3.pdf"],
}


def _parse_entities(entities):
    parsed = {"act": [], "company": [], "year": [], "text": [], "numeric": []}
    for entity in entities or []:
        raw = str(entity.get("text", "")).strip()
        if not raw:
            continue
        label, value = "", raw
        if ":" in raw:
            label, value = raw.split(":", 1)
            label = label.strip().lower()
            value = value.strip()
        value = value.rstrip(".").strip()
        if not value or value.lower() == "none":
            continue
        value_lc = value.lower()

        if label == "act":
            parsed["act"].append(value_lc)
        elif label == "company":
            parsed["company"].append(value_lc)
        elif label == "year":
            parsed["year"].append(value_lc)
        elif value.isdigit() or re.match(r'^\d+[a-z]?$', value_lc):
            parsed["numeric"].append(value_lc)
        elif len(value_lc) >= MIN_KEYWORD_LENGTH:
            parsed["text"].append(value_lc)
    return parsed


def _search_legal(graph, parsed):
    text_keywords = parsed["text"]
    numeric_keywords = parsed["numeric"]

    allowed_sources = None
    for act_value in parsed["act"]:
        for act_name, sources in ACT_SOURCE_MAP.items():
            if act_name in act_value or act_value in act_name:
                allowed_sources = set(sources) if allowed_sources is None else allowed_sources | set(sources)

    if not text_keywords and not numeric_keywords and allowed_sources is None:
        return []

    results = []
    seen = set()
    for node_id, data in graph.graph.nodes(data=True):
        if data.get("type") != "SourcePassage":
            continue

        source = str(data.get("source", ""))
        if allowed_sources is not None and source not in allowed_sources:
            continue

        excerpt = str(data.get("excerpt", ""))
        haystack = excerpt.lower()
        text_match = any(k in haystack for k in text_keywords) if text_keywords else True

        node_number = str(data.get("section", data.get("article", ""))).lower()
        numeric_match = any(node_number == nk for nk in numeric_keywords) if numeric_keywords else True

        if numeric_keywords:
            if not numeric_match:
                continue
        else:
            if not text_match:
                continue

        key = (data.get("source"), data.get("page"), data.get("section"), data.get("article"))
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "node": node_id,
            "type": "SourcePassage",
            "source": data.get("source", ""),
            "page": data.get("page"),
            "section": data.get("section") or data.get("article"),
            "excerpt": data.get("excerpt", ""),
            "relationship": "Act -> Section/Article -> Page -> Passage",
        })

    results.sort(key=lambda item: (item["page"] or 0, str(item["section"])))
    return results


def _search_corporate(graph, parsed):
    company_keywords = parsed["company"]
    year_keywords = parsed["year"]
    text_keywords = parsed["text"]

    if not company_keywords and not year_keywords and not text_keywords:
        return []

    allowed_filing_sources = None

    if company_keywords:
        allowed_filing_sources = set()
        for node_id, data in graph.graph.nodes(data=True):
            if data.get("type") != "Company":
                continue
            company_name = str(data.get("name", "")).lower()
            if not any(ck in company_name or company_name in ck for ck in company_keywords):
                continue
            for _, target, edge_data in graph.graph.out_edges(node_id, data=True):
                target_data = graph.graph.nodes[target]
                if target_data.get("type") == "Filing":
                    allowed_filing_sources.add(target_data.get("source"))

    if year_keywords:
        year_filtered = set()
        for node_id, data in graph.graph.nodes(data=True):
            if data.get("type") != "Filing":
                continue
            filing_year = str(data.get("year", ""))
            if any(yk in filing_year for yk in year_keywords):
                if allowed_filing_sources is None or data.get("source") in allowed_filing_sources:
                    year_filtered.add(data.get("source"))
        if allowed_filing_sources is not None or year_keywords:
            allowed_filing_sources = year_filtered if year_filtered else (allowed_filing_sources or set())

    results = []
    seen = set()
    for node_id, data in graph.graph.nodes(data=True):
        if data.get("type") != "CorpPassage":
            continue

        source = data.get("source")
        if allowed_filing_sources is not None and source not in allowed_filing_sources:
            continue

        excerpt = str(data.get("excerpt", ""))
        haystack = excerpt.lower()
        if text_keywords and not any(k in haystack for k in text_keywords):
            continue

        key = (source, data.get("page"))
        if key in seen:
            continue
        seen.add(key)

        results.append({
            "node": node_id,
            "type": "CorpPassage",
            "source": source,
            "page": data.get("page"),
            "section": None,
            "excerpt": excerpt,
            "relationship": "Company -> Filing -> Page -> Passage",
        })

    results.sort(key=lambda item: (item["source"] or "", item["page"] or 0))
    return results


def graph_search(state):
    domain = state.get("domain")
    if domain not in ("indian_law", "corporate"):
        return {"graph_results": []}

    graph = VeriDocGraph(storage_path="data/graph_store.pkl")
    parsed = _parse_entities(state.get("entities", []))

    if domain == "indian_law":
        results = _search_legal(graph, parsed)
    else:
        results = _search_corporate(graph, parsed)

    return {"graph_results": results[:10]}
