"""
Module 2 - Graph State
The shared dictionary every LangGraph node reads from and writes to.
Defined first because every node's function signature depends on it.
"""
import operator
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    NotRequired,
    Optional,
    TypedDict,
)
from langchain_core.documents import Document
from pydantic import BaseModel, Field


# ============================================================================
# 1. EXISTING VERIDOC 1.0 C-RAG & PROOFLOOP STATE (UNTOUCHED)
# ============================================================================
class RAGState(TypedDict):
    question: str
    query: str
    docs: list
    scores: any
    answer: str
    grade: str
    retries: int
    # Entity & Graph retrieval fields:
    entities: list        # For extract_entities.py
    graph_results: list   # For graph_search.py

    # Domain-aware routing and legal-research metadata.
    domain: NotRequired[str]
    question_type: NotRequired[str]
    jurisdiction: NotRequired[str]
    legal_entities: NotRequired[List[Dict[str, Any]]]
    temporal_scope: NotRequired[List[str]]
    source_filters: NotRequired[Dict[str, Any]]

    # Structured ProofLoop response metadata.
    evidence_status: NotRequired[str]
    evidence_confidence: NotRequired[float]
    evidence: NotRequired[List[Dict[str, Any]]]


# ============================================================================
# 2. VERIDOC 2.0 STRUCTURED PYDANTIC SCHEMAS (DECOMPOSITION, AUDIT & CRITIC)
# ============================================================================
class ExtractedClaim(BaseModel):
    """Single verifiable clause, SLA metric, or financial line item extracted from a target document."""
    claim_id: str = Field(description="Unique identifier e.g. CLM-01")
    claim_type: Literal["semantic_policy", "numeric_financial", "sla_deadline"] = Field(
        description="Routes to C-RAG ProofLoop if semantic, or Deterministic Audit if numeric/SLA"
    )
    section_title: str = Field(description="Clause heading or invoice line-item label")
    raw_text: str = Field(description="Exact verbatim clause or line item from target document")
    numeric_value: Optional[float] = Field(
        default=None,
        description="Extracted number (fee %, SLA %, dollar amount, or days) if present",
    )
    unit: Optional[str] = Field(default=None, description="USD, percent, days, etc.")
    baseline_query: str = Field(
        description="Targeted question sent into RAGState.question to verify against master baseline docs"
    )


class DecompositionOutput(BaseModel):
    """Structured output returned by the Decomposition Planner node."""
    document_summary: str
    extracted_claims: List[ExtractedClaim]


class AuditFinding(BaseModel):
    """Verified finding produced by each parallel worker combining Deterministic Math + ProofLoop C-RAG."""
    claim_id: str
    claim_type: str
    section_title: str
    status: Literal["COMPLIANT", "VIOLATION", "ANOMALY_FLAGGED", "UNVERIFIED"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    reasoning: str
    deterministic_metrics: Optional[Dict[str, Any]] = None
    # Directly maps from your RAGState ProofLoop fields:
    evidence_status: Optional[str] = None
    evidence_confidence: Optional[float] = None
    proof_evidence: Optional[List[Dict[str, Any]]] = None
    sha256_provenance_hash: Optional[str] = None
    critic_approved: bool = True
    critic_feedback: Optional[str] = None


class CriticReview(BaseModel):
    """Structured output for Module 4 Evaluator-Optimizer reflection node."""
    approved: bool = Field(description="True only if finding has valid SHA-256 provenance and zero contradictions")
    feedback: str = Field(description="Correction instructions if rejected")
    adjusted_severity: Optional[Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]] = None


# ============================================================================
# 3. VERIDOC 2.0 LANGGRAPH MULTI-AGENT ORCHESTRATOR STATES
# ============================================================================
class ClaimWorkerState(TypedDict):
    """Isolated state sent to each parallel worker via LangGraph Send() API."""
    claim: Dict[str, Any]
    historical_series: List[float]
    baseline_limits: Dict[str, float]
    findings: Annotated[List[Dict[str, Any]], operator.add]


class AuditOrchestratorState(TypedDict, total=False):
    """Parent Multi-Agent State orchestrating Decomposition, Parallel Workers, Critic, Guardrails & HITL."""
    # Input payload
    target_doc_id: str
    target_doc_text: str
    sanitized_doc_text: str                 # Populated by Module 7 Sandwich Input Guardrail
    historical_series: List[float]          # Used by Module 3 Deterministic Z-score & IQR engine
    baseline_limits: Dict[str, float]       # Deterministic caps e.g. {"max_late_fee_pct": 5.0, "min_sla_uptime": 99.5}

    # Guardrail & Security state (Module 7)
    guardrail_passed: bool
    pii_redacted_count: int
    injection_detected: bool

    # Planner & Parallel Map-Reduce state (Modules 1, 2, 3)
    extracted_claims: List[Dict[str, Any]]
    findings: Annotated[List[Dict[str, Any]], operator.add]  # Parallel reducer merges worker outputs

    # Evaluator-Optimizer Critic state (Module 4)
    critic_retries: int
    verified_findings: List[Dict[str, Any]]

    # Synthesis & Human-in-the-Loop Remediation state (Module 5)
    risk_score: float
    executive_report: str
    remediation_payload: Dict[str, Any]
    human_approval_status: Literal["PENDING", "APPROVED", "EDITED", "REJECTED"]
    human_reviewer_notes: Optional[str]

    # LLMOps Telemetry state (Module 6)
    telemetry: Dict[str, Any]