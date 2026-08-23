"""
Baseline graph for before/after comparison — plain RAG, no grading,
no rewrite loop. Straight retrieve -> rerank -> generate.
"""
from langgraph.graph import StateGraph, START, END
from app.core.state import RAGState
from app.graph.nodes.retrieve import retrieve
from app.graph.nodes.rerank import rerank
from app.graph.nodes.generate import generate


def build_baseline_graph():
    builder = StateGraph(RAGState)
    builder.add_node("retrieve", retrieve)
    builder.add_node("rerank", rerank)
    builder.add_node("generate", generate)

    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


baseline_graph = build_baseline_graph()