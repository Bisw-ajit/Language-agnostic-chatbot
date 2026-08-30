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

    return {
        "raw_query": query,
        "normalized_query": normalized_query,
        "search_query": rewritten_query,
        "is_follow_up": is_follow_up,
        "language_info": lang_info
    }
