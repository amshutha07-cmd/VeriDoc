"""
Router — the conditional edge logic deciding generate vs rewrite.
This branch is the thing a plain LangChain chain cannot do.
"""
from app.core.state import RAGState
from app.core.config import settings


def route(state: RAGState) -> str:
    if state["grade"] == "useful" or state.get("retries", 0) >= settings.max_retries:
        return "generate"
    return "rewrite"


if __name__ == "__main__":
    # sanity check both branches without needing a real graph
    useful_state: RAGState = {"question": "", "query": "", "docs": [], "scores": None,
                               "answer": "", "grade": "useful", "retries": 0}
    weak_state: RAGState = {"question": "", "query": "", "docs": [], "scores": None,
                             "answer": "", "grade": "not_useful", "retries": 0}
    maxed_state: RAGState = {"question": "", "query": "", "docs": [], "scores": None,
                              "answer": "", "grade": "not_useful", "retries": 2}

    print("grade=useful       ->", route(useful_state))    # expect: generate
    print("grade=not_useful   ->", route(weak_state))      # expect: rewrite
    print("retries maxed out  ->", route(maxed_state))     # expect: generate