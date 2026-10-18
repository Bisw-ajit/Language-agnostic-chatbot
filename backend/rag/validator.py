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
    "documents": {
        "document", "documents", "aadhaar", "card", "passbook", "dastavez", "certificate", "praman", "dalil", "ro r", "ror", "proof",
        # Devanagari
        "दस्तावेज", "दस्तावेज़", "आधार", "कार्ड", "पासबुक", "प्रमाणपत्र", "प्रमाण",
        # Odia
        "କାଗଜପତ୍ର", "ଦଲିଲ", "ପ୍ରମାଣପତ୍ର", "ଆଧାର", "କାର୍ଡ", "ପାସବୁକ୍"
    },
    "eligibility": {
        "eligibility", "eligible", "criteria", "patrata", "patra", "yogyata", "who", "resident", "condition", "rules", "age",
        # Devanagari
        "पात्रता", "पात्र", "योग्यता", "कौन", "आयु", "उम्र", "शर्त", "नियम",
        # Odia
        "ଯୋଗ୍ୟତା", "ଯୋଗ୍ୟ", "ସର୍ତ୍ତାବଳୀ", "କିଏ", "ବୟସ", "ନିୟମ"
    },
    "benefits": {
        "benefit", "benefits", "amount", "money", "rupees", "rs", "lakh", "coverage", "pension", "cashless", "sahayata", "rashi",
        # Devanagari
        "लाभ", "राशि", "रुपये", "पैसे", "सहायता", "पेंशन", "कवरेज", "कितना", "कितनी",
        # Odia
        "ଲାଭ", "ସହାୟତା", "ଟଙ୍କା", "ରାଶି", "ପେନସନ", "କେତେ", "ସୁବିଧା"
    },
    "procedure": {
        "apply", "application", "procedure", "how", "process", "portal", "website", "form", "aavedan", "kare", "kaise",
        "allot", "allotment", "selection", "committee", "criteria", "modalities", "mechanism", "guidelines", "instructions",
        "engagement", "procurement", "supply", "assigned", "entrusted", "steps", "distribution", "approval", "tender", "contract",
        # Devanagari
        "आवेदन", "प्रक्रिया", "कैसे", "पोर्टल", "वेबसाइट", "फॉर्म", "पंजीकरण", "आवंटन", "चयन", "नियम", "निर्देश",
        # Odia
        "ଆବେଦନ", "କିପରି", "ପ୍ରକ୍ରିୟା", "ପୋର୍ଟାଲ", "ୱେବସାଇଟ", "ଫର୍ମ", "କେମିତି", "ଚୟନ", "ବଣ୍ଟନ", "ନିର୍ଦ୍ଦେଶାବଳୀ"
    }
}

# Domain vocabulary for government welfare schemes and policies across supported languages
DOMAIN_TERMS = {
    # Core Welfare Schemes (English)
    "kalia", "scheme", "schemes", "yojana", "bsky", "mbpy", "pension", "scholarship", "scholarships",
    "odisha", "farmer", "farmers", "assistance", "biju", "swasthya", "kalyan", "madhu",
    "babu", "post", "matric", "portal", "guidelines", "policy", "merit", "benefit", "benefits", "eligibility",
    "document", "documents", "apply", "application", "financial", "aid", "allowance", "hospital",
    "cashless", "treatment", "landless", "agriculture", "income", "limit", "rules", "criteria",
    # Women & Child Development / Mission Shakti
    "mission", "shakti", "wshg", "wshgs", "shg", "shgs", "uniform", "uniforms", "commodity", "commodities",
    "procurement", "supply", "fisheries", "osfdc", "child", "children", "welfare",
    # Agriculture & Irrigation Schemes
    "mkuy", "pdmc", "drip", "sprinkler", "irrigation", "krushi", "udyog", "disaster", "dmp", "millets", "samruddhi", "balaram",
    # Social Security & Disabilities
    "abadana", "nfbs", "banishree", "orpwd", "disability", "disabilities", "special", "needs", "senior", "citizens",
    # ST & SC Development & Forestry
    "emrs", "eklavya", "residential", "fra", "forest", "dwellers", "tribal", "caste", "certificate", "certificates",
    # School & Mass Education
    "mo", "school", "abhiyan", "pathani", "samanta", "mathematics", "talent",
    # Hindi / Hinglish
    "कालिया", "योजना", "बीजू", "स्वास्थ्य", "कल्याण", "मधु", "बाबू", "पेंशन", "छात्रवृत्ति",
    "स्कॉलरशिप", "मैट्रिक", "पोर्टल", "सहायता", "किसान", "किसानों", "दस्तावेज", "पात्रता",
    "आवेदन", "लाभ", "राशि", "रुपये", "पैसे", "ओडिशा", "अस्पताल", "इलाज", "कार्ड", "दिशा-निर्देश",
    "मिशन", "शक्ति", "वर्दी", "यूनिफॉर्म", "स्कूल", "आबंटन", "कृषि", "उद्योग",
    "sahayata", "kisan", "patrata", "dastavez", "aavedan", "rashi", "praman", "yogyata", "kaam", "allot",
    # Odia
    "କାଳିଆ", "ଯୋଜନା", "ବିଜୁ", "ସ୍ୱାସ୍ଥ୍ୟ", "କଲ୍ୟାଣ", "ମଧୁ", "ବାବୁ", "ପେନସନ", "ଛାତ୍ରବୃତ୍ତି",
    "ସ୍କଲାରସିପ୍", "ପୋର୍ଟାଲ", "ସହାୟତା", "ଚାଷୀ", "କୃଷକ", "କାଗଜପତ୍ର", "ଦଲିଲ", "ପ୍ରମାଣପତ୍ର",
    "ଯୋଗ୍ୟତା", "ଆବେଦନ", "ଓଡ଼ିଶା", "ଚିକିତ୍ସା", "ଡାକ୍ତରଖାନା", "ଟଙ୍କା", "ରାଶି", "କାର୍ଡ",
    "ଭୂମିହୀନ", "ବୟସ", "ସୀମା", "ଖାତା", "ନିୟମ", "ସର୍ତ୍ତାବଳୀ", "ମିଶନ", "ଶକ୍ତି", "ପୋଷାକ", "ୟୁନିଫର୍ମ", "ବିଦ୍ୟାଳୟ"
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
            # Normalize scheme title by stripping years, version markers, and digits
            base1 = re.sub(r'\b(19\d\d|20\d\d|v\d+|version\s*\d+|\d+\.\d+)\b', '', t1, flags=re.IGNORECASE)
            base1 = re.sub(r'[\-_/]+', ' ', base1)
            base1 = re.sub(r'\s+', ' ', base1).strip().lower()

            base2 = re.sub(r'\b(19\d\d|20\d\d|v\d+|version\s*\d+|\d+\.\d+)\b', '', t2, flags=re.IGNORECASE)
            base2 = re.sub(r'[\-_/]+', ' ', base2)
            base2 = re.sub(r'\s+', ' ', base2).strip().lower()

            if base1 == base2 and t1 != t2:
                diff = doc_amounts[t1].symmetric_difference(doc_amounts[t2])
                if diff:
                    conflicts.append(f"Discrepancy detected between '{t1}' and '{t2}' regarding amounts: {', '.join(diff)}")

    return len(conflicts) > 0, conflicts

def check_intent_coverage(query: str, sources: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Checks whether specific intent dimensions in the user query (e.g. documents, eligibility)
    are addressed by the retrieved evidence.

    Returns:
        (is_fully_covered: bool, missed_intents: List[str])
        - is_fully_covered: True if all detected intents are covered by sources
        - missed_intents: list of intent names NOT covered by retrieved sources
    """
    query_tokens = set(tokenize_multilingual(query.lower()))
    if not query_tokens or not sources:
        return True, []

    # Check domain relevance
    has_domain = bool(query_tokens.intersection(DOMAIN_TERMS))

    # Determine user intent dimensions
    detected_intents = []
    for intent_name, keywords in INTENT_KEYWORDS.items():
        if query_tokens.intersection(keywords):
            detected_intents.append(intent_name)

    if not has_domain:
        return False, ["domain_mismatch"]

    if not detected_intents:
        # General informational query within domain
        return True, []

    # Check if retrieved sources cover those intents
    combined_source_text = " ".join([
        s.get("text", "").lower() + " " + s.get("section", "").lower()
        for s in sources
    ])
    source_tokens = set(tokenize_multilingual(combined_source_text))

    missed_intents = []
    for intent_name in detected_intents:
        keywords = INTENT_KEYWORDS[intent_name]
        if not source_tokens.intersection(keywords):
            missed_intents.append(intent_name)

    is_fully_covered = len(missed_intents) == 0
    return is_fully_covered, missed_intents


def _intent_coverage_score(query: str, sources: List[Dict[str, Any]]) -> float:
    """
    Internal helper that returns a float coverage ratio [0.0, 1.0]
    for use in composite evidence scoring inside validate_evidence().
    """
    query_tokens = set(tokenize_multilingual(query.lower()))
    if not query_tokens or not sources:
        return 0.5

    has_domain = bool(query_tokens.intersection(DOMAIN_TERMS))

    detected_intents = []
    for intent_name, keywords in INTENT_KEYWORDS.items():
        if query_tokens.intersection(keywords):
            detected_intents.append(intent_name)

    if not has_domain:
        return 0.05

    if not detected_intents:
        return 0.85

    combined_source_text = " ".join([
        s.get("text", "").lower() + " " + s.get("section", "").lower()
        for s in sources
    ])
    source_tokens = set(tokenize_multilingual(combined_source_text))

    covered = sum(
        1 for intent_name in detected_intents
        if source_tokens.intersection(INTENT_KEYWORDS[intent_name])
    )
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
    intent_coverage = _intent_coverage_score(query or "", sources) if query else 0.85

    # 4. Multi-Signal Evidence Score
    composite_evidence_score = round(
        (max_score * 0.45 + avg_relevance * 0.25 + avg_authority * 0.15 + intent_coverage * 0.15),
        3
    )

    # 5. Contradiction Detection
    has_conflict, conflicts = detect_contradictions(sources)

    # Determine Evidence Level with language-calibrated thresholds
    is_odia = (target_language == "or" or bool(re.search(r'[\u0B00-\u0B7F]', query or "")))
    min_confidence = 0.18 if is_odia else settings.confidence_threshold
    min_composite = 0.20 if is_odia else 0.25

    if max_score < min_confidence or composite_evidence_score < min_composite or (intent_coverage < 0.30 and max_score < 0.45):
        return False, composite_evidence_score, "INSUFFICIENT", fallback_msg, conflicts
    elif composite_evidence_score >= 0.70 and len(sources) >= 2:
        return True, composite_evidence_score, "HIGH", "", conflicts
    else:
        return True, composite_evidence_score, "MEDIUM", "", conflicts
