"""
Module 2 — Graph State
The shared dictionary every LangGraph node reads from and writes to.
Defined first because every node's function signature depends on it.
"""
from typing import TypedDict, List, Optional
from langchain_core.documents import Document


class RAGState(TypedDict):
    question: str               # original user question, never overwritten
    query: str                    # active search query (starts = question, changes on rewrite)
    docs: List[Document]          # retrieved chunks
    scores: Optional[List[float]] # rerank/relevance scores, parallel to docs — used by Differentiator 1 later
    answer: str                    # final generated answer
    grade: str                      # "useful" or "not_useful"
    retries: int                     # loop guard, stops rewrite from running forever