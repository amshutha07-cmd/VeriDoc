"""
Shared prompt-building helpers used across graph nodes.
"""
from langchain_core.documents import Document
from typing import List


def format_ctx(docs: List[Document]) -> str:
    """Tag each chunk with its source so downstream nodes can cite it."""
    return "\n\n".join(
        f"[{d.metadata.get('source', 'unknown')} p{d.metadata.get('page_label', '?')}]\n{d.page_content}"
        for d in docs
    )