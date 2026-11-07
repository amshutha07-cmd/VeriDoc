# backend/app/graph/nodes/fast_grader.py
import math
import re
import threading
import time
from typing import Any, Dict, List

_GRADER_LOCK = threading.Lock()

try:
    from sentence_transformers import CrossEncoder
    _FAST_ENCODER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
except Exception:
    _FAST_ENCODER = None


def grade_claim_evidence_fast(query: str, evidence_spans: List[str]) -> Dict[str, Any]:
    """Thread-safe local Cross-Encoder relevance grader for parallel LangGraph workers."""
    t0 = time.perf_counter()
    if not evidence_spans:
        return {"relevant": False, "score": 0.0, "latency_ms": 0.0, "grader_type": "empty"}

    combined_span = " ".join(evidence_spans[:3])[:1500]

    if _FAST_ENCODER is not None:
        try:
            with _GRADER_LOCK:
                raw_score = float(_FAST_ENCODER.predict([(query, combined_span)])[0])
            prob = 1.0 / (1.0 + math.exp(-raw_score))
            grader_type = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        except Exception:
            q_tokens = set(re.findall(r"\w+", query.lower()))
            s_tokens = set(re.findall(r"\w+", combined_span.lower()))
            overlap = len(q_tokens & s_tokens) / max(len(q_tokens), 1)
            prob = round(min(overlap * 1.5, 1.0), 4)
            grader_type = "lexical-overlap-fallback"
    else:
        q_tokens = set(re.findall(r"\w+", query.lower()))
        s_tokens = set(re.findall(r"\w+", combined_span.lower()))
        overlap = len(q_tokens & s_tokens) / max(len(q_tokens), 1)
        prob = round(min(overlap * 1.5, 1.0), 4)
        grader_type = "lexical-overlap-fallback"

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "relevant": prob >= 0.45,
        "score": round(prob, 4),
        "latency_ms": latency_ms,
        "grader_type": grader_type,
    }
