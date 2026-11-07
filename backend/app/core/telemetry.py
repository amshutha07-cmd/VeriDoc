# backend/app/core/telemetry.py
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

_CACHE_STORE: Dict[str, Dict[str, Any]] = {}
_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "audit_telemetry.jsonl"


def get_clause_cache_key(raw_text: str, baseline_limits: Dict[str, float]) -> str:
    """Computes a normalized SHA-256 key over clause text and policy thresholds."""
    normalized_text = " ".join(raw_text.strip().lower().split())
    limits_str = json.dumps(baseline_limits, sort_keys=True)
    payload = f"{normalized_text}||{limits_str}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def lookup_cached_finding(cache_key: str) -> Optional[Dict[str, Any]]:
    return _CACHE_STORE.get(cache_key)


def store_cached_finding(cache_key: str, finding: Dict[str, Any]) -> None:
    _CACHE_STORE[cache_key] = finding


def clear_clause_cache() -> None:
    _CACHE_STORE.clear()


def build_telemetry_summary(
    start_time: float,
    total_claims: int,
    cache_hits: int,
    worker_failures: int,
    doc_text: str,
) -> Dict[str, Any]:
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    est_input_tokens = max(len(doc_text) // 4, 1) + (total_claims - cache_hits) * 350
    est_output_tokens = (total_claims - cache_hits) * 180
    # Blended Llama-3.3-70B / GPT-4o-mini cost estimate ($0.60 / 1M tokens)
    est_cost_usd = round(((est_input_tokens + est_output_tokens) / 1_000_000) * 0.60, 6)

    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_latency_ms": elapsed_ms,
        "total_claims": total_claims,
        "cache_hits": cache_hits,
        "cache_misses": max(total_claims - cache_hits, 0),
        "cache_hit_rate_pct": round((cache_hits / max(total_claims, 1)) * 100, 2),
        "worker_failures": worker_failures,
        "estimated_tokens": est_input_tokens + est_output_tokens,
        "estimated_cost_usd": est_cost_usd,
    }
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass
    return record