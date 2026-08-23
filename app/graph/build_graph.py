# """
# Module 8 — Wire the Graph
# Assembles all nodes into the actual LangGraph state machine.
# Uses grade_docs_v2 (Differentiator 1) as the default grader, since it's
# the version we validated catches real grading failures the base misses.
# """
# from langgraph.graph import StateGraph, START, END
# from app.core.state import RAGState
# from app.graph.nodes.retrieve import retrieve
# from app.graph.nodes.rerank import rerank
# from app.graph.nodes.grade import grade_docs_v2 as grade_docs   # Differentiator 1 wired as default
# from app.graph.nodes.rewrite import rewrite
# from app.graph.nodes.generate import generate
# from app.graph.router import route


# def build_graph():
#     builder = StateGraph(RAGState)
#     builder.add_node("retrieve", retrieve)
#     builder.add_node("rerank", rerank)
#     builder.add_node("grade_docs", grade_docs)
#     builder.add_node("rewrite", rewrite)
#     builder.add_node("generate", generate)

#     builder.add_edge(START, "retrieve")
#     builder.add_edge("retrieve", "rerank")
#     builder.add_edge("rerank", "grade_docs")
#     builder.add_conditional_edges("grade_docs", route,
#         {"generate": "generate", "rewrite": "rewrite"})
#     builder.add_edge("rewrite", "retrieve")
#     builder.add_edge("generate", END)

#     return builder.compile()


# graph = build_graph()


# if __name__ == "__main__":
#     result = graph.invoke({
#         "question": "What are Apple's main risk factors?",
#         "query": "", "docs": [], "scores": None,
#         "answer": "", "grade": "", "retries": 0,
#     })
#     print("FINAL ANSWER:\n", result["answer"])
#     print("\nRetries used:", result["retries"])
#     print("Final grade:", result["grade"])
"""
Module 8 — Wire the Graph
Module 9 — Memory + Streaming
Assembles all nodes into the LangGraph state machine, with a checkpointer
for multi-turn memory and replay, and stream() support for SSE later.
Uses grade_docs_v2 (Differentiator 1) as the default grader.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.core.state import RAGState
from app.graph.nodes.retrieve import retrieve
from app.graph.nodes.rerank import rerank
from app.graph.nodes.grade import grade_docs_v2 as grade_docs
from app.graph.nodes.rewrite import rewrite
from app.graph.nodes.generate import generate
from app.graph.router import route


def build_graph():
    builder = StateGraph(RAGState)
    builder.add_node("retrieve", retrieve)
    builder.add_node("rerank", rerank)
    builder.add_node("grade_docs", grade_docs)
    builder.add_node("rewrite", rewrite)
    builder.add_node("generate", generate)

    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "grade_docs")
    builder.add_conditional_edges("grade_docs", route,
        {"generate": "generate", "rewrite": "rewrite"})
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("generate", END)

    return builder.compile(checkpointer=MemorySaver())


graph = build_graph()


def _blank_state(question: str) -> dict:
    return {
        "question": question, "query": "", "docs": [], "scores": None,
        "answer": "", "grade": "", "retries": 0,
    }


if __name__ == "__main__":
    cfg = {"configurable": {"thread_id": "test-session-1"}}

    print("=== Turn 1: invoke ===")
    result1 = graph.invoke(_blank_state("What are Apple's main risk factors?"), cfg)
    print("ANSWER:\n", result1["answer"][:300])
    print("Retries:", result1["retries"], "| Grade:", result1["grade"])

    print("\n=== Turn 2: stream (node-by-node) ===")
    for step in graph.stream(_blank_state("What did they say about supply chain risk?"), cfg):
        print("completed node:", list(step.keys()))

    print("\n=== Replay: fetching checkpoint history for this thread ===")
    history = list(graph.get_state_history(cfg))
    print(f"Found {len(history)} checkpoint(s) for thread_id='test-session-1'")