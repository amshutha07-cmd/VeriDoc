"""
Module 2 — Graph State
The shared dictionary every LangGraph node reads from and writes to.
Defined first because every node's function signature depends on it.
"""
from typing import TypedDict, List, Optional, NotRequired, Dict, Any
from langchain_core.documents import Document


class RAGState(TypedDict):
    question: str
    query: str
    docs: List[Document]
    scores: Optional[List[float]]
    answer: str
    grade: str
    retries: int

    # Structured ProofLoop response metadata.
    evidence_status: NotRequired[str]
    evidence_confidence: NotRequired[float]
    evidence: NotRequired[List[Dict[str, Any]]]
