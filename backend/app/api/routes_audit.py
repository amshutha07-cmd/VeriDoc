# backend/app/api/routes_audit.py
import hashlib
import hmac
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from app.graph.audit_graph import build_audit_orchestrator_graph
from app.core.telemetry import build_telemetry_summary

router = APIRouter(prefix="/api/audit", tags=["Autonomous Multi-Agent Audit"])
audit_graph = build_audit_orchestrator_graph(use_hitl_interrupt=True)

DB_PATH = Path(__file__).resolve().parent.parent / "audit_ledger.db"
WEBHOOK_SECRET = b"veridoc-secret-prod-2026-key"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_ledger (
            thread_id TEXT PRIMARY KEY,
            target_doc_id TEXT,
            idempotency_key TEXT UNIQUE,
            risk_score REAL,
            dispatch_status TEXT,
            payload TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()


class AuditRequest(BaseModel):
    target_doc_id: str = Field(default="DOC-2026-001")
    target_doc_text: str = Field(..., description="Raw text of contract, policy, or invoice to audit")
    historical_series: List[float] = Field(
        default_factory=lambda: [1200.0, 1250.0, 1180.0, 1220.0, 1210.0, 1240.0],
    )
    baseline_limits: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {"max_late_fee_pct": 5.0, "min_sla_uptime": 99.5}
    )


class HITLApproveRequest(BaseModel):
    thread_id: str
    decision: str = Field(default="APPROVED", description="APPROVED, EDITED, or REJECTED")
    reviewer_notes: Optional[str] = Field(default="Approved by Human Compliance Lead")


@router.post("/run")
async def run_autonomous_audit(payload: AuditRequest):
    try:
        t0 = time.perf_counter()
        thread_id = f"audit-{uuid.uuid4().hex[:8]}"
        config = {
            "configurable": {"thread_id": thread_id},
            "max_concurrency": 5,
            "recursion_limit": 25,
        }
        initial_state = {
            "target_doc_id": payload.target_doc_id,
            "target_doc_text": payload.target_doc_text,
            "historical_series": payload.historical_series,
            "baseline_limits": payload.baseline_limits,
            "findings": [],
            "critic_retries": 0,
        }
        final_state = await audit_graph.ainvoke(initial_state, config=config)
        findings = final_state.get("verified_findings") or final_state.get("findings", [])
        cache_hits = sum(
            1 for f in findings if (f.get("deterministic_metrics") or {}).get("cache_hit") is True
        )
        telemetry = build_telemetry_summary(
            start_time=t0,
            total_claims=len(findings),
            cache_hits=cache_hits,
            worker_failures=0,
            doc_text=payload.target_doc_text,
        )

        resp = {
            "status": "awaiting_human_approval",
            "thread_id": thread_id,
            "target_doc_id": payload.target_doc_id,
            "guardrail_summary": {
                "guardrail_passed": final_state.get("guardrail_passed", True),
                "pii_redacted_count": final_state.get("pii_redacted_count", 0),
                "injection_detected": final_state.get("injection_detected", False),
            },
            "telemetry": telemetry,
            "extracted_claims_count": len(final_state.get("extracted_claims", [])),
            "risk_score": final_state.get("risk_score", 0.0),
            "findings": findings,
            "remediation_payload": final_state.get("remediation_payload", {}),
            "executive_report": final_state.get("executive_report", ""),
        }

        # Persist to SQLite WAL Ledger
        rem_payload = final_state.get("remediation_payload", {})
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """INSERT OR REPLACE INTO audit_ledger (thread_id, target_doc_id, idempotency_key, risk_score, dispatch_status, payload)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                thread_id,
                payload.target_doc_id,
                rem_payload.get("idempotency_key", f"idem-{thread_id}"),
                final_state.get("risk_score", 0.0),
                "PENDING_APPROVAL",
                str(resp),
            ),
        )
        conn.commit()
        conn.close()
        return resp
    except Exception as exc:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audit orchestration failed: {str(exc)}")


@router.post("/approve")
async def approve_hitl_remediation(payload: HITLApproveRequest):
    try:
        config = {"configurable": {"thread_id": payload.thread_id}}
        snapshot = audit_graph.get_state(config)
        existing_payload = dict((snapshot.values or {}).get("remediation_payload") or {})
        idem_key = existing_payload.get("idempotency_key", f"idem-{payload.thread_id}")

        # Check SQLite Ledger for Idempotency Replay Protection
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT dispatch_status FROM audit_ledger WHERE idempotency_key = ?", (idem_key,))
        row = cur.fetchone()
        
        if row and row[0] == "WEBHOOK_DISPATCHED":
            conn.close()
            existing_payload["dispatch_status"] = "SKIPPED_DUPLICATE_IDEMPOTENT_REPLAY"
            return {
                "status": "idempotent_replay_blocked",
                "thread_id": payload.thread_id,
                "human_approval_status": snapshot.values.get("human_approval_status", "APPROVED"),
                "remediation_payload": existing_payload,
            }

        audit_graph.update_state(
            config,
            {
                "human_approval_status": payload.decision,
                "human_reviewer_notes": payload.reviewer_notes,
            },
        )
        resumed_state = await audit_graph.ainvoke(None, config=config)
        resumed_payload = resumed_state.get("remediation_payload", {})
        resumed_payload["dispatch_status"] = "WEBHOOK_DISPATCHED"

        # Compute Real HMAC-SHA256 Signature for Webhook Dispatch
        payload_bytes = str(resumed_payload).encode("utf-8")
        signature = hmac.new(WEBHOOK_SECRET, payload_bytes, hashlib.sha256).hexdigest()
        resumed_payload["webhook_signature_sha256"] = f"sha256={signature}"

        cur.execute(
            "UPDATE audit_ledger SET dispatch_status = ?, payload = ? WHERE thread_id = ?",
            ("WEBHOOK_DISPATCHED", str(resumed_payload), payload.thread_id),
        )
        conn.commit()
        conn.close()

        return {
            "status": "remediation_completed",
            "thread_id": payload.thread_id,
            "human_approval_status": resumed_state.get("human_approval_status"),
            "remediation_payload": resumed_payload,
        }
    except Exception as exc:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"HITL resume failed: {str(exc)}")
