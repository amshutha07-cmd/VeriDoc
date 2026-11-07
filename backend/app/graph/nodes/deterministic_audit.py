# backend/app/graph/nodes/deterministic_audit.py
import hashlib
import math
import re
import statistics
from typing import Any, Dict, List, Optional

# Deterministic Indian Tax & Statutory Lookup Tables
HSN_SAC_GST_RATES: Dict[str, float] = {
    "998314": 18.0,  # IT Design & Development Services
    "998315": 18.0,  # Cloud & Hosting Infrastructure Services
    "998313": 18.0,  # IT Consulting & Support
    "997331": 18.0,  # Software Licensing
}

TDS_SECTION_RATES: Dict[str, float] = {
    "194c": 2.0,     # Contractual payments to domestic vendors
    "194j": 10.0,    # Professional or technical services
    "194i": 10.0,    # Rent of plant/machinery/office
}

GSTIN_REGEX = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
GST_CANDIDATE_REGEX = re.compile(r"GSTIN\s*[:=-]?\s*([A-Z0-9]{10,18})", re.IGNORECASE)
PAN_CANDIDATE_REGEX = re.compile(r"PAN\s*[:=-]?\s*([A-Z0-9]{8,12})", re.IGNORECASE)


def compute_sha256_span(text: str) -> str:
    """Generates a deterministic 64-char SHA-256 hash for verifiable span provenance."""
    normalized = " ".join(text.strip().split()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def verify_gstin_checksum(gstin: str) -> bool:
    """Validates 15-character Indian GSTIN format, state code (01-38), and Modulo-36 check digit."""
    if not GSTIN_REGEX.match(gstin):
        return False
    state_code = int(gstin[:2])
    if not (1 <= state_code <= 38):
        return False
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    total = 0
    for idx, ch in enumerate(gstin[:14]):
        val = chars.index(ch)
        factor = 2 if idx % 2 == 1 else 1
        prod = val * factor
        total += (prod // 36) + (prod % 36)
    check_code = (36 - (total % 36)) % 36
    return gstin[14] == chars[check_code]


def run_indian_compliance_checks(raw_text: str) -> Dict[str, Any]:
    """Runs deterministic Indian tax, GSTIN, PAN, SAC/HSN GST rate, and TDS section checks."""
    violations: List[str] = []
    details: Dict[str, Any] = {}

    # 1. GSTIN format & state/checksum verification
    gst_match = GST_CANDIDATE_REGEX.search(raw_text)
    if gst_match:
        cand = gst_match.group(1).upper()
        is_valid_format = bool(GSTIN_REGEX.match(cand)) and (1 <= int(cand[:2]) <= 38 if cand[:2].isdigit() else False)
        details["gstin_candidate"] = cand
        details["gstin_valid"] = is_valid_format
        if not is_valid_format:
            violations.append(f"Invalid Indian GSTIN '{cand}' (failed 15-char state/PAN structure check)")

    # 2. PAN format verification
    pan_match = PAN_CANDIDATE_REGEX.search(raw_text)
    if pan_match:
        p_cand = pan_match.group(1).upper()
        p_valid = bool(PAN_REGEX.match(p_cand))
        details["pan_candidate"] = p_cand
        details["pan_valid"] = p_valid
        if not p_valid:
            violations.append(f"Invalid Indian PAN '{p_cand}' (must match 5 letters, 4 digits, 1 letter)")

    # 3. SAC / HSN Code vs. statutory GST percentage check
    sac_match = re.search(r"(?:SAC|HSN)\s*(?:Code)?\s*[:#-]?\s*(\d{4,6})", raw_text, re.IGNORECASE)
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*GST|GST\s*(?:of|@|:)?\s*(\d+(?:\.\d+)?)\s*%", raw_text, re.IGNORECASE)
    if sac_match and pct_match:
        code = sac_match.group(1)
        charged_gst = float(pct_match.group(1) or pct_match.group(2))
        expected_gst = HSN_SAC_GST_RATES.get(code)
        details["sac_code"] = code
        details["charged_gst_pct"] = charged_gst
        if expected_gst is not None and abs(charged_gst - expected_gst) > 1e-4:
            details["expected_gst_pct"] = expected_gst
            violations.append(
                f"SAC/HSN {code} statutory GST rate is {expected_gst}%, but invoice billed {charged_gst}%"
            )

    # 4. Income Tax Act TDS Section check (194C / 194J / 194I)
    tds_match = re.search(r"Section\s+(194[CJI])\b", raw_text, re.IGNORECASE)
    tds_pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*TDS|TDS\s*(?:of|@|:)?\s*(\d+(?:\.\d+)?)\s*%", raw_text, re.IGNORECASE)
    if tds_match and tds_pct_match:
        sec = tds_match.group(1).lower()
        applied_tds = float(tds_pct_match.group(1) or tds_pct_match.group(2))
        expected_tds = TDS_SECTION_RATES.get(sec)
        details["tds_section"] = sec.upper()
        details["applied_tds_pct"] = applied_tds
        if expected_tds is not None and abs(applied_tds - expected_tds) > 1e-4:
            details["expected_tds_pct"] = expected_tds
            violations.append(
                f"Income Tax Section {sec.upper()} mandates {expected_tds}% TDS, but contract/invoice applied {applied_tds}%"
            )

    return {"violations": violations, "details": details}


def verify_upstream_extraction(llm_value: Optional[float], raw_text: str) -> Dict[str, Any]:
    if llm_value is None:
        return {"verified": True, "regex_values": [], "extraction_mismatch": False}

    cleaned_text = re.sub(r"^Section\s+\d+(?:\.\d+)?", "", raw_text.strip(), flags=re.IGNORECASE)
    span_matches = re.findall(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", cleaned_text)

    parsed_candidates = [float(m.replace(",", "")) for m in span_matches]
    is_match = any(abs(llm_value - cand) < 1e-4 for cand in parsed_candidates)

    return {
        "verified": is_match,
        "llm_extracted_value": llm_value,
        "regex_candidates": parsed_candidates,
        "extraction_mismatch": not is_match,
    }


def compute_z_score_iqr_and_mad(value: float, series: List[float]) -> Dict[str, Any]:
    if not series or len(series) < 4:
        return {
            "evaluated_value": value,
            "z_score": 0.0,
            "modified_z_score_mad": 0.0,
            "iqr_outlier": False,
            "mean": value,
            "median": value,
            "mad": 0.0,
            "std_dev": 0.0,
            "iqr_bounds": [value, value],
            "is_statistical_anomaly": False,
        }

    mean = sum(series) / len(series)
    variance = sum((x - mean) ** 2 for x in series) / len(series)
    std_dev = math.sqrt(variance) if variance > 0 else 1e-9
    z_score = (value - mean) / std_dev

    med = statistics.median(series)
    abs_devs = [abs(x - med) for x in series]
    mad = statistics.median(abs_devs)
    modified_z_mad = (0.6745 * abs(value - med)) / (mad if mad > 0 else 1e-9)

    sorted_s = sorted(series)
    n = len(sorted_s)
    q1 = sorted_s[n // 4]
    q3 = sorted_s[(3 * n) // 4]
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    iqr_outlier = value < lower_bound or value > upper_bound

    return {
        "evaluated_value": round(value, 4),
        "mean": round(mean, 4),
        "median": round(med, 4),
        "std_dev": round(std_dev, 4),
        "mad": round(mad, 4),
        "z_score": round(z_score, 4),
        "modified_z_score_mad": round(modified_z_mad, 4),
        "iqr_bounds": [round(lower_bound, 4), round(upper_bound, 4)],
        "is_statistical_anomaly": (abs(z_score) > 2.5 or modified_z_mad > 3.5 or iqr_outlier),
    }


def run_deterministic_check(
    claim: Dict[str, Any],
    historical_series: List[float],
    baseline_limits: Dict[str, float],
) -> Dict[str, Any]:
    val = claim.get("numeric_value")
    raw_text = claim.get("raw_text", "")
    section_title = claim.get("section_title", "")
    combined_text = f"{section_title} {raw_text}".lower()
    claim_type = claim.get("claim_type", "")
    provenance_hash = compute_sha256_span(raw_text)

    extraction_check = verify_upstream_extraction(val, raw_text)
    india_checks = run_indian_compliance_checks(raw_text)

    violations: List[str] = list(india_checks["violations"])
    metrics: Dict[str, Any] = {
        "evaluated_value": val,
        "extraction_verification": extraction_check,
    }
    if india_checks["details"]:
        metrics["indian_statutory_checks"] = india_checks["details"]

    if val is None:
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "metrics": metrics,
            "sha256": provenance_hash,
        }

    if extraction_check["extraction_mismatch"]:
        violations.append(
            f"Upstream extraction mismatch: LLM extracted {val} but deterministic regex found {extraction_check['regex_candidates']}"
        )

    is_fee_clause = any(k in combined_text for k in ("late", "penalty", "interest", "overdue"))
    is_sla_clause = (
        claim_type == "sla_deadline"
        or any(k in combined_text for k in ("sla", "uptime", "service level", "availability"))
    )
    is_tax_clause = any(k in combined_text for k in ("gst", "tds", "sac", "hsn", "194c", "194j"))
    is_currency_spend = (
        ("$" in raw_text or "₹" in raw_text or "inr" in combined_text or "usd" in combined_text or "charge" in combined_text or "retainer" in combined_text)
        and not is_fee_clause
        and not is_sla_clause
        and not is_tax_clause
    )

    if is_fee_clause:
        max_fee = baseline_limits.get("max_late_fee_pct", 5.0)
        metrics["policy_cap_pct"] = max_fee
        metrics["delta_pct"] = round(val - max_fee, 4)
        if val > max_fee:
            violations.append(
                f"Value {val}% exceeds deterministic policy cap of {max_fee}% (Delta: +{round(val - max_fee, 2)}%)"
            )

    if is_sla_clause:
        min_sla = baseline_limits.get("min_sla_uptime", 99.5)
        metrics["mandatory_min_sla_pct"] = min_sla
        metrics["deficit_pct"] = round(min_sla - val, 4)
        if val < min_sla:
            violations.append(
                f"SLA {val}% falls below mandatory minimum {min_sla}% (Deficit: -{round(min_sla - val, 2)}%)"
            )

    if is_currency_spend:
        stats = compute_z_score_iqr_and_mad(val, historical_series)
        metrics.update(stats)
        if stats["is_statistical_anomaly"]:
            violations.append(
                f"Statistical spend anomaly: z={stats['z_score']}, mad_z={stats['modified_z_score_mad']}, outside IQR {stats['iqr_bounds']}"
            )

    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "metrics": metrics,
        "sha256": provenance_hash,
    }