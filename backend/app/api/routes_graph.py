from fastapi import APIRouter, Request
from app.limiter import limiter
from pydantic import BaseModel
from app.graph.build_graph import graph
from app.api.routes_ask import _blank_state

router = APIRouter(prefix="/graph", tags=["graph"])

class GraphSearchRequest(BaseModel):
    question: str
    thread_id: str = "graph-ui"

@router.post("/search")
@limiter.limit("10/minute")
def graph_search(request: Request, req: GraphSearchRequest):
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

@router.get("/explore")
@limiter.limit("30/minute")
def graph_explore(request: Request):
    from app.graph_store.graph_handler import VeriDocGraph
    g = VeriDocGraph(storage_path="data/graph_store.pkl")
    nodes = [
        {"id": n, **data}
        for n, data in g.graph.nodes(data=True)
    ]
    edges = [
        {"from": u, "to": v, **data}
        for u, v, data in g.graph.edges(data=True)
    ]
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }
