import re
from typing import List, Dict, Any, Tuple, Optional
from backend.config import get_settings
from backend.rag.prompts import FALLBACK_MESSAGES
from backend.language.normalizer import tokenize_multilingual

AUTHORITY_WEIGHTS = {
    "official": 1.0,
    "trusted": 0.95,
    "demo": 0.90,
    "user_uploaded": 0.80,
    "unknown": 0.60
}

INTENT_KEYWORDS = {
    "documents": {"document", "documents", "aadhaar", "card", "passbook", "dastavez", "certificate", "praman", "dalil", "ro r", "ror", "proof"},
    "eligibility": {"eligibility", "eligible", "criteria", "patrata", "patra", "yogyata", "who", "resident", "condition", "rules"},
    "benefits": {"benefit", "benefits", "amount", "money", "rupees", "rs", "lakh", "coverage", "pension", "cashless", "sahayata", "rashi"},
    "procedure": {"apply", "application", "procedure", "how", "process", "portal", "website", "form", "aavedan", "kare", "kaise"}
}

def detect_contradictions(sources: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Detects potential conflicting numerical amounts or facts across retrieved document sources.
    Returns (has_contradiction, list_of_conflict_details).
    """
    if len(sources) < 2:
        return False, []

    conflicts = []
    # Extract scheme monetary amounts per document
    doc_amounts: Dict[str, set] = {}
    for s in sources:
        doc_title = s.get("document_title", "Doc")
        text = s.get("text", "")
        # Find amounts like Rs 10000, Rs 5000, 5 Lakh
        amounts = set(re.findall(r'(?:Rs\.?|₹)\s*\d+|(?:Rs\.?|₹)?\s*\d+\s*(?:Lakh|Crore|Hajar|K)', text, re.IGNORECASE))
        if amounts:
            if doc_title not in doc_amounts:
                doc_amounts[doc_title] = set()
            doc_amounts[doc_title].update(amounts)

    # Check for diverging versions of the same scheme title
    titles = list(doc_amounts.keys())
    for i in range(len(titles)):
        for j in range(i + 1, len(titles)):
            t1, t2 = titles[i], titles[j]
            # If same base scheme name across different versions
            base1 = t1.split("v")[0].strip()
            base2 = t2.split("v")[0].strip()
            if base1.lower() == base2.lower() and t1 != t2:
                diff = doc_amounts[t1].symmetric_difference(doc_amounts[t2])
                if diff:
                    conflicts.append(f"Discrepancy detected between '{t1}' and '{t2}' regarding amounts: {', '.join(diff)}")

    return len(conflicts) > 0, conflicts

def check_intent_coverage(query: str, sources: List[Dict[str, Any]]) -> float:
    """
    Checks whether specific intent dimensions in the user query (e.g. documents, eligibility)
    are addressed by the retrieved evidence.
    """
    query_tokens = set(tokenize_multilingual(query.lower()))
    if not query_tokens or not sources:
        return 0.5

    # Determine user intent dimensions
    detected_intents = []
    for intent_name, keywords in INTENT_KEYWORDS.items():
        if query_tokens.intersection(keywords):
            detected_intents.append(intent_name)

    if not detected_intents:
        # General informational query
        return 0.9

    # Check if retrieved sources cover those intents
    combined_source_text = " ".join([s.get("text", "").lower() + " " + s.get("section", "").lower() for s in sources])
    source_tokens = set(tokenize_multilingual(combined_source_text))

    covered = 0
    for intent_name in detected_intents:
        keywords = INTENT_KEYWORDS[intent_name]
        if source_tokens.intersection(keywords):
            covered += 1

    return covered / len(detected_intents)

def validate_evidence(
    sources: List[Dict[str, Any]],
    target_language: str,
    query: Optional[str] = None
) -> Tuple[bool, float, str, str, List[str]]:
    """
    Multi-signal evidence validator assessing:
    1. Maximum & average retrieval relevance scores
    2. Number of supporting document chunks
    3. Source authority level weighting
    4. Query intent coverage
    5. Contradiction detection

    Returns (is_sufficient, evidence_score, evidence_level, fallback_message, conflict_warnings)
    where evidence_level is 'HIGH', 'MEDIUM', or 'INSUFFICIENT'.
    """
    settings = get_settings()
    fallback_msg = FALLBACK_MESSAGES.get(target_language, FALLBACK_MESSAGES["en"])
    
    if not sources:
        return False, 0.0, "INSUFFICIENT", fallback_msg, []

    # 1. Relevance Signals
    scores = [float(s.get("score", 0.0)) for s in sources]
    max_score = max(scores, default=0.0)
    top3_scores = sorted(scores, reverse=True)[:3]
    avg_relevance = sum(top3_scores) / len(top3_scores)

    # 2. Authority Signal
    auth_scores = [AUTHORITY_WEIGHTS.get(s.get("authority_level", "official"), 0.7) for s in sources]
    avg_authority = sum(auth_scores) / len(auth_scores)

    # 3. Intent Coverage Signal
    intent_coverage = check_intent_coverage(query or "", sources) if query else 0.85

    # 4. Multi-Signal Evidence Score
    composite_evidence_score = round(
        (max_score * 0.45 + avg_relevance * 0.25 + avg_authority * 0.15 + intent_coverage * 0.15),
        3
    )

    # 5. Contradiction Detection
    has_conflict, conflicts = detect_contradictions(sources)

    # Determine Evidence Level
    if max_score < settings.confidence_threshold or composite_evidence_score < 0.25 or intent_coverage < 0.30:
        return False, composite_evidence_score, "INSUFFICIENT", fallback_msg, conflicts
    elif composite_evidence_score >= 0.70 and len(sources) >= 2:
        return True, composite_evidence_score, "HIGH", "", conflicts
    else:
        return True, composite_evidence_score, "MEDIUM", "", conflicts
