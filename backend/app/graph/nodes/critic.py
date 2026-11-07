# backend/app/graph/nodes/critic.py
from typing import Any, Dict, List
from app.guardrails.sandwich_guard import verify_output_provenance


def evaluate_findings_critic_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluator-Optimizer Critic Node:
    Audits parallel worker findings for schema completeness, SHA-256 provenance,
    and logical consistency between deterministic metrics and status labels.
    """
    raw_findings: List[Dict[str, Any]] = state.get("findings", [])
    checked_findings = verify_output_provenance(raw_findings)

    verified_findings: List[Dict[str, Any]] = []
    for f in checked_findings:
        metrics = f.get("deterministic_metrics") or {}
        status = f.get("status")

        if metrics.get("delta_pct", 0) > 0 and status == "COMPLIANT":
            f["status"] = "VIOLATION"
            f["severity"] = "CRITICAL"
            f["critic_feedback"] = "Critic auto-corrected status from COMPLIANT to VIOLATION based on positive fee delta."
        elif metrics.get("deficit_pct", 0) > 0 and status == "COMPLIANT":
            f["status"] = "VIOLATION"
            f["severity"] = "CRITICAL"
            f["critic_feedback"] = "Critic auto-corrected status from COMPLIANT to VIOLATION based on SLA deficit."
        else:
            f["critic_approved"] = True
            f["critic_feedback"] = "Verified by Evaluator-Optimizer Critic: SHA-256 provenance and math bounds aligned."

        verified_findings.append(f)

    return {
        "verified_findings": verified_findings,
        "critic_retries": state.get("critic_retries", 0) + 1,
    }