"""Small deterministic source filter for explicitly named legal instruments."""
import re
from langchain_core.documents import Document


def filter_legal_sources(query: str, docs: list[Document]) -> list[Document]:
    normalized = query.lower()
    anchors = re.findall(r"\barticle\s+\d+[a-z]?\b", normalized)
    if "106th" in normalized and "amendment" in normalized or "one hundred and sixth" in normalized and "amendment" in normalized:
        anchors.extend(["106th amendment", "one hundred and sixth amendment", "article 334a", "article 330a", "article 332a"])
    if not anchors:
        return docs
    scored = []
    for doc in docs:
        source = str(doc.metadata.get("source", doc.metadata.get("filename", "")))
        content = f"{source} {doc.page_content}".lower()
        scored.append((sum(anchor in content for anchor in anchors), doc))
    best = max((score for score, _ in scored), default=0)
    return [doc for score, doc in scored if score == best] if best else docs
