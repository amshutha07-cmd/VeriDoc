"""
POST /ask — streams the graph's node-by-node execution as Server-Sent Events.
"""
import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from app.graph.build_graph import graph

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    thread_id: str = "default"


def _blank_state(question: str) -> dict:
    return {
        "question": question, "query": "", "docs": [], "scores": None,
        "answer": "", "grade": "", "retries": 0,
    }


@router.post("/ask")
async def ask(req: AskRequest):
    cfg = {"configurable": {"thread_id": req.thread_id}}

    async def event_generator():
        try:
            for step in graph.stream(_blank_state(req.question), cfg):
                node_name = list(step.keys())[0]
                node_output = step[node_name]

                payload = {"node": node_name}
                if "docs" in node_output:
                    payload["docs"] = [
                        {"source": d.metadata.get("source"), "page": d.metadata.get("page_label")}
                        for d in node_output["docs"]
                    ]
                if "grade" in node_output:
                    payload["grade"] = node_output["grade"]
                if "retries" in node_output:
                    payload["retries"] = node_output["retries"]
                if "answer" in node_output:
                    payload["answer"] = node_output["answer"]

                yield {"event": "node", "data": json.dumps(payload)}

            yield {"event": "done", "data": "{}"}

        except Exception as e:
            # send a clean error event instead of letting the connection die silently
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(event_generator())