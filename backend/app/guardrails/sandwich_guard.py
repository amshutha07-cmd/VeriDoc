# backend/app/guardrails/sandwich_guard.py
import re
from typing import Any, Dict, List

PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "PHONE": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "INDIAN_PAN": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
    "SSN_OR_TAX_ID": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*override", re.IGNORECASE),
    re.compile(r"mark\s+all\s+(?:clauses|invoices|claims)\s+as\s+compliant", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+(?:developer|dan|unrestricted)\s+mode", re.IGNORECASE),
    re.compile(r"approve\s+all\s+invoices\s+immediately", re.IGNORECASE),
    re.compile(r"set\s+risk_score\s*(?:to|=)\s*0", re.IGNORECASE),
    re.compile(r"bypass\s+(?:all\s+)?(?:audit|compliance|security)\s+checks", re.IGNORECASE),
    re.compile(r"print\s+(?:your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"disregard\s+baseline\s+policy", re.IGNORECASE),
    re.compile(r"\[hidden[\s_-]*instruction\]", re.IGNORECASE),
    re.compile(r"auto_approve\s*=\s*true", re.IGNORECASE),
]


def run_input_guardrail(raw_text: str) -> Dict[str, Any]:
    """Redacts sensitive PII and blocks indirect prompt injections hidden in documents."""
    sanitized = raw_text
    redacted_count = 0

    for label, pattern in PII_PATTERNS.items():
        matches = pattern.findall(sanitized)
        redacted_count += len(matches)
        sanitized = pattern.sub(f"[REDACTED_{label}]", sanitized)

    injection_hits: List[str] = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(sanitized):
            injection_hits.append(pattern.pattern)
            sanitized = pattern.sub("[BLOCKED_PROMPT_INJECTION]", sanitized)

    return {
        "sanitized_doc_text": sanitized,
        "pii_redacted_count": redacted_count,
        "injection_detected": len(injection_hits) > 0,
        "guardrail_passed": len(injection_hits) == 0,
    }


def verify_output_provenance(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Output guardrail ensuring every finding carries a 64-char SHA-256 span hash."""
    verified: List[Dict[str, Any]] = []
    for item in findings:
        sha = item.get("sha256_provenance_hash") or ""
        if len(sha) != 64:
            item["status"] = "UNVERIFIED"
            item["critic_approved"] = False
            item["critic_feedback"] = "Blocked by Output Guardrail: Missing valid 64-char SHA-256 provenance hash."
        verified.append(item)
    return verified