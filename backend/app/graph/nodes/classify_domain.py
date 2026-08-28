import re
from typing import Any, Dict

from app.core.state import RAGState


LEGAL_TERMS = {
    "act", "acts", "section", "sections", "rule", "rules", "judgment",
    "judgement", "court", "petition", "statute", "law", "legal",
    "constitution", "article", "ipc", "bns", "crpc", "bnss", "cpc",
    "amendment", "precedent", "writ", "bail", "offence", "offense",
    "jurisdiction", "evidence act", "contract act", "supreme court",
    "high court",
}

COMPARISON_TERMS = {
    "compare", "comparison", "changed", "change", "difference", "before",
    "after", "year over year", "across years", "versus", "vs",
}


def _has_term(text: str, terms: set[str]) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    normalized = " ".join(re.findall(r"[a-z0-9]+", text.lower()))

    for term in terms:
        if " " in term:
            if term in normalized:
                return True
        elif term in tokens:
            return True
    return False


def classify_domain(state: RAGState) -> Dict[str, Any]:
    question = state.get("question", "")
    text = question.lower()
    is_legal = _has_term(text, LEGAL_TERMS)
    domain = "indian_law" if is_legal else "corporate"

    if _has_term(text, COMPARISON_TERMS):
        question_type = "comparison"
    elif is_legal and _has_term(text, {"section", "article", "rule", "act"}):
        question_type = "provision_lookup"
    elif is_legal and _has_term(text, {"judgment", "judgement", "court", "precedent"}):
        question_type = "judgment_analysis"
    elif is_legal:
        question_type = "legal_general"
    else:
        question_type = "corporate_research"

    print(f"Domain classified: {domain} | Question type: {question_type}")
    return {
        "domain": domain,
        "question_type": question_type,
        "jurisdiction": "India" if is_legal else "",
    }
