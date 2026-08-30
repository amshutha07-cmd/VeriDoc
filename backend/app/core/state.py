"""
Module 2 - Graph State
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

    # Domain-aware routing and legal-research metadata.
    domain: NotRequired[str]
    question_type: NotRequired[str]
    jurisdiction: NotRequired[str]
    legal_entities: NotRequired[List[Dict[str, Any]]]
    temporal_scope: NotRequired[List[str]]
    source_filters: NotRequired[Dict[str, Any]]

    # Structured ProofLoop response metadata.
    evidence_status: NotRequired[str]
    evidence_confidence: NotRequired[float]
    evidence: NotRequired[List[Dict[str, Any]]]

