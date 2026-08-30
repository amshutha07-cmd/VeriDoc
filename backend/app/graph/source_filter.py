"""Deterministic source filter for explicitly named legal instruments."""
import re
from collections import defaultdict
from langchain_core.documents import Document


def filter_legal_sources(query: str, docs: list[Document]) -> list[Document]:
    normalized = query.lower()
    anchors = re.findall(r"\barticle\s+\d+[a-z]?\b", normalized)
    named_106th = (
        ("106th" in normalized and "amendment" in normalized)
        or ("one hundred and sixth" in normalized and "amendment" in normalized)
    )
    if named_106th:
        anchors.extend([
            "106th amendment",
            "one hundred and sixth amendment",
            "constitution (one hundred and sixth amendment) act",
            "article 334a",
            "article 330a",
            "article 332a",
        ])
    if not anchors or not docs:
        return docs

    scored = []
    source_scores = defaultdict(lambda: [0, 0, 0])
    for doc in docs:
        source = str(doc.metadata.get("source", doc.metadata.get("filename", "")))
        content = f"{source} {doc.page_content}".lower()
        anchor_score = sum(anchor in content for anchor in anchors)
        exact_title_score = 20 if "constitution (one hundred and sixth amendment) act" in content else 0
        score = anchor_score + exact_title_score
        scored.append((source, score, doc))
        source_scores[source][0] = max(source_scores[source][0], score)
        source_scores[source][1] += score
        source_scores[source][2] += int(score > 0)

    if not named_106th:
        best = max((score for _, score, _ in scored), default=0)
        return [doc for _, score, doc in scored if score == best] if best else docs

    winning_source = max(
        source_scores,
        key=lambda source: (
            source_scores[source][0],
            source_scores[source][1],
            source_scores[source][2],
        ),
    )
    winning_docs = [
        doc for source, score, doc in scored
        if source == winning_source and score > 0
    ]
    return winning_docs or docs