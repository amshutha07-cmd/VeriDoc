from fastapi import APIRouter
from pydantic import BaseModel
from app.graph.build_graph import graph
from app.api.routes_ask import _blank_state

router = APIRouter(prefix="/graph", tags=["graph"])

class GraphSearchRequest(BaseModel):
    question: str
    thread_id: str = "graph-ui"

@router.post("/search")
def graph_search(req: GraphSearchRequest):
    state = graph.invoke(_blank_state(req.question), {"configurable": {"thread_id": req.thread_id}})
    results = state.get("graph_results", []) or []
    return {
        "question": req.question,
        "nodes": results,
        "edges": [
            {
                "from": item.get("node"),
                "to": f"{item.get('source', 'source')}::p{item.get('page', '?')}",
                "relationship": item.get("relationship", "Act ? Section ? Page ? Passage"),
            }
            for item in results
        ],
        "status": "connected" if results else "no_graph_results",
    }