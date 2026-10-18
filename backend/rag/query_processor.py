import re
from typing import List, Dict, Any, Optional
from backend.language.normalizer import normalize_text
from backend.language.detector import detect_language_structured

# Pronouns or generic referential indicators in English, Hindi/Hinglish, and Odia
FOLLOW_UP_INDICATORS = {
    "it", "this", "that", "the scheme", "these", "its", "they", "them",
    "yeh", "ye", "is", "iska", "iske", "iski", "us", "uska", "uske", "iski", "yojana",
    "ଏହା", "ଏହାର", "ଏହି", "ସେହି", "ଯୋଜନା", "ସେଥିପାଇଁ"
}

# Cross-lingual scheme name & concept mappings to bridge Odia/Hindi queries to English administrative docs
MULTILINGUAL_ENTITY_MAP = {
    # Pathani Samanta Mathematics
    "ପଠାଣି": "Pathani Samanta Mathematics",
    "ସାମନ୍ତ": "Pathani Samanta",
    "ଗଣିତ": "Mathematics",
    "पठानी": "Pathani Samanta Mathematics",
    "सामंत": "Pathani Samanta",
    "गणित": "Mathematics",
    
    # KALIA
    "କାଳିଆ": "KALIA Krushak Assistance",
    "କାଲିଆ": "KALIA Krushak Assistance",
    "कालिया": "KALIA Krushak Assistance",
    
    # BSKY
    "ବିଜୁ": "Biju Swasthya Kalyan BSKY",
    "ସ୍ୱାସ୍ଥ୍ୟ": "Swasthya Health HealthCard",
    "बीजू": "Biju Swasthya Kalyan BSKY",
    "स्वास्थ्य": "Swasthya Health HealthCard",
    
    # Madhu Babu Pension
    "ମଧୁ": "Madhu Babu Pension MBPY",
    "ବାବୁ": "Madhu Babu",
    "ପେନସନ": "Pension",
    "मधु": "Madhu Babu Pension MBPY",
    "बाबू": "Madhu Babu",
    "पेंशन": "Pension",
    
    # Scholarships & Education
    "ଛାତ୍ରବୃତ୍ତି": "Scholarship",
    "छात्रवृत्ति": "Scholarship",
    "ମେଧାବୃତ୍ତି": "Merit Scholarship",
    "ପୋଷ୍ଟ": "Post Matric",
    "ମାଟ୍ରିକ": "Matric",
    "ଇକଲବ୍ୟ": "Eklavya EMRS School",
    "ଏକଲବ୍ୟ": "Eklavya EMRS School",
    "ମୋ ସ୍କୁଲ": "Mo School Abhiyan",
    "କୃଷି": "Krushi Agriculture MKUY",
    "ଉଦ୍ୟୋଗ": "Udyog Industry",
    "ମିଶନ ଶକ୍ତି": "Mission Shakti WSHG",
    "ବନିଶ୍ରୀ": "Banishree Scholarship Special Needs",
    "ଅବଦାନ": "ABADANA Senior Citizens",
    
    # Common Intent terms
    "ଯୋଗ୍ୟତା": "eligibility criteria",
    "पात्रता": "eligibility criteria",
    "ଲାଭ": "benefits financial assistance",
    "लाभ": "benefits financial assistance",
    "ସହାୟତା": "financial assistance allowance",
    "सहायता": "financial assistance allowance",
    "ଆବେଦନ": "how to apply application procedure",
    "आवेदन": "how to apply application procedure",
    "କାଗଜପତ୍ର": "required documents",
    "दस्तावेज": "required documents"
}

def process_and_rewrite_query(
    query: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    user_preference: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes the raw query:
    1. Normalizes unicode & whitespace
    2. Detects language and script
    3. Analyzes conversation history for contextual query expansion/rewriting
    """
    normalized_query = normalize_text(query)
    lang_info = detect_language_structured(normalized_query, user_preference=user_preference)
    
    rewritten_query = normalized_query
    is_follow_up = False

    if conversation_history and len(conversation_history) > 0:
        words = set(re.findall(r'[\w\u0900-\u097F\u0B00-\u0B7F]+', normalized_query.lower()))
        # Check if query contains referential pronouns or is short (< 6 words) without explicit scheme name
        has_indicator = bool(words.intersection(FOLLOW_UP_INDICATORS))
        is_short = len(words) <= 6

        if has_indicator or is_short:
            # Extract main entities / topics from previous user messages or assistant responses
            previous_topics = []
            for msg in reversed(conversation_history[-4:]):
                prev_text = msg.get("content", "")
                # Extract potential scheme / policy names
                matches = re.findall(r'([A-Z][a-zA-Z0-9\s]+(?:Yojana|Scheme|Policy|Scholarship|Portal|Pension|BSKY|KALIA))', prev_text, re.IGNORECASE)
                if matches:
                    previous_topics.extend(matches)
                    break
            
            if previous_topics:
                topic = previous_topics[0].strip()
                # If topic isn't already mentioned in the query, append for search clarity
                if topic.lower() not in normalized_query.lower():
                    rewritten_query = f"{normalized_query} for {topic}"
                    is_follow_up = True

    # Cross-lingual semantic bridging: append canonical English names when Odia/Hindi terms are present
    english_expansions = []
    for term, eng in MULTILINGUAL_ENTITY_MAP.items():
        if term in normalized_query:
            for word in eng.split():
                if word.lower() not in rewritten_query.lower() and word not in english_expansions:
                    english_expansions.append(word)

    if english_expansions:
        search_query = f"{rewritten_query} {' '.join(english_expansions[:6])}"
    else:
        search_query = rewritten_query

    return {
        "raw_query": query,
        "normalized_query": normalized_query,
        "search_query": search_query,
        "is_follow_up": is_follow_up,
        "language_info": lang_info
    }
