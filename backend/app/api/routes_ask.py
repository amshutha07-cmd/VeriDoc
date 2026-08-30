"""
POST /ask - streams the graph's node-by-node execution as Server-Sent Events.
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
        "question": question,
        "query": "",
        "docs": [],
        "scores": None,
        "answer": "",
        "grade": "",
        "retries": 0,
        "entities": [],
        "graph_results": [],
        "domain": "corporate",
        "question_type": "general",
        "jurisdiction": "",
        "legal_entities": [],
        "temporal_scope": [],
        "source_filters": {},
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
                for field in (
                     "domain",
                     "question_type",
                     "jurisdiction",
                     "entities",
                     "graph_results",
                ):
                  if field in node_output:
                    payload[field] = node_output[field]
  
                if "docs" in node_output:
                    payload["docs"] = [
                         {
                            "source": d.metadata.get("source", "unknown"),
                            "page": d.metadata.get(
                                "page_label",
                                d.metadata.get("page"),
                            ),
                            "excerpt": " ".join(str(d.page_content)[:400].split()),
                            "organization": d.metadata.get("organization", "Unknown"),
                            "category": d.metadata.get("category", "Unknown"),
                            "document_type": d.metadata.get("document_type", "Unknown"),
                            "publication_year": d.metadata.get("publication_year"),
                         }
                    for d in node_output["docs"]
                    ]
                
                if "grade" in node_output:
                    payload["grade"] = node_output["grade"]
                if "retries" in node_output:
                    payload["retries"] = node_output["retries"]
                if "answer" in node_output:
                    payload["answer"] = node_output["answer"]
                if "evidence_status" in node_output:
                    payload["evidence_status"] = node_output["evidence_status"]
                if "evidence_confidence" in node_output:
                    payload["evidence_confidence"] = node_output["evidence_confidence"]

                if "evidence" in node_output:
                    payload["evidence"] = node_output["evidence"]


                yield {"event": "node", "data": json.dumps(payload)}

            yield {"event": "done", "data": "{}"}

        except Exception as e:
            # send a clean error event instead of letting the connection die silently
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(event_generator())


def _json_evidence(documents: list) -> list[dict]:
    return [
        {
            "source": d.metadata.get("source", d.metadata.get("filename", "unknown")),
            "page": d.metadata.get("page_label", d.metadata.get("page", d.metadata.get("page_number"))),
            "excerpt": " ".join(str(d.page_content)[:400].split()),
            "organization": d.metadata.get("organization", "Unknown"),
            "category": d.metadata.get("category", "Evidence"),
            "document_type": d.metadata.get("document_type", "Unknown"),
            "publication_year": d.metadata.get("publication_year"),
        }
        for d in documents
    ]


@router.post("/ask/json")
async def ask_json(req: AskRequest):
    cfg = {"configurable": {"thread_id": req.thread_id}}
    try:
        final_state = graph.invoke(_blank_state(req.question), cfg)
        documents = final_state.get("docs", []) or []
        evidence = _json_evidence(documents)
        return {
            "answer": final_state.get("answer", "") or "",
            "evidence": evidence,
            "docs": evidence,
            "grade": final_state.get("grade", ""),
            "scores": final_state.get("scores"),
            "retries": final_state.get("retries", 0),
            "domain": final_state.get("domain", ""),
            "question_type": final_state.get("question_type", ""),
            "model": final_state.get("model", ""),
            "graph_results": final_state.get("graph_results", []),
        }
    except Exception as exc:
        return {"answer": "", "evidence": [], "docs": [], "error": str(exc)}
