"""
Module 2 â€” Graph State
The shared dictionary every LangGraph node reads from and writes to.
Defined first because every node's function signature depends on it.
"""
from typing import TypedDict, List, Optional, NotRequired, Dict, Any
from langchain_core.documents import Document


class RAGState(TypedDict):
    question: str
    query: str
    docs: list
    scores: any
    answer: str
    grade: str
    retries: int
    # ADD THESE TWO LINES:
    entities: list        # For extract_entities.py
    graph_results: list   # For graph_search.py

    # Structured ProofLoop response metadata.
    evidence_status: NotRequired[str]
    evidence_confidence: NotRequired[float]
    evidence: NotRequired[List[Dict[str, Any]]]
