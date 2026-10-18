import re
import unicodedata
from typing import List, Set

# Common Odia nominal and locative case suffixes (ordered longest to shortest)
ODIA_SUFFIXES = [
    "ମାନଙ୍କର", "ମାନଙ୍କୁ", "ଗୁଡ଼ିକର", "ଗୁଡିକର", "ଗୁଡ଼ିକ", "ଗୁଡିକ", 
    "ମାନେ", "ଙ୍କର", "ଙ୍କୁ", "ଠାରୁ", "ଠାରେ", "ଦ୍ୱାରା", "ରେ", "କୁ", "ର"
]

# Canonical Hinglish phonetic and colloquial mappings
HINGLISH_CANONICAL = {
    "kyaa": "kya", "kia": "kya",
    "chaiye": "chahiye", "chahie": "chahiye", "chahye": "chahiye",
    "muje": "mujhe", "mujhey": "mujhe",
    "krna": "karna", "kare": "karna", "karein": "karna",
    "h": "hai", "hain": "hai",
    "konse": "kaun", "kaunse": "kaun",
    "paise": "paisa", "rupaye": "rupay",
    "dastawez": "dastavez", "dastavej": "dastavez",
    "kese": "kaise", "kayse": "kaise", "btao": "batao"
}

def normalize_text(text: str) -> str:
    """
    Normalizes text for downstream processing:
    - NFKC unicode normalization
    - Strips excessive whitespace
    - Preserves Devanagari, Odia, and Latin characters
    """
    if not text:
        return ""
    
    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    
    # Replace carriage returns, tabs, and non-breaking spaces
    text = re.sub(r'[\r\n\t\u00A0]+', ' ', text)
    
    # Strip excessive spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def stem_odia_token(token: str) -> str:
    """
    Applies rule-based suffix stemming for Odia nouns and verbs.
    Removes common postpositions and plural/case markers if stem length >= 2.
    """
    if not token or len(token) <= 3:
        return token
    for suffix in ODIA_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 2:
            return token[:-len(suffix)]
    return token

def normalize_hinglish_token(token: str) -> str:
    """
    Normalizes phonetic and spelling variations in Romanized Hindi (Hinglish).
    """
    return HINGLISH_CANONICAL.get(token.lower(), token.lower())

def tokenize_multilingual(text: str, include_stems: bool = True) -> List[str]:
    """
    Tokenizes text across English, Hindi, Hinglish, and Odia.
    Splits on punctuation and whitespace, preserving unicode words and numbers.
    Optionally includes morphological stems (for Odia) and canonical forms (for Hinglish).
    """
    normalized = normalize_text(text).lower()
    raw_tokens = re.findall(r'[\w\u0900-\u097F\u0B00-\u0B7F]+', normalized)
    
    if not include_stems:
        return raw_tokens

    enriched_tokens = []
    for t in raw_tokens:
        enriched_tokens.append(t)
        
        # Odia inflection handling
        if re.search(r'[\u0B00-\u0B7F]', t):
            stemmed = stem_odia_token(t)
            if stemmed != t:
                enriched_tokens.append(stemmed)
                
        # Hinglish canonical token handling
        elif t in HINGLISH_CANONICAL:
            canonical = normalize_hinglish_token(t)
            if canonical != t:
                enriched_tokens.append(canonical)

    return enriched_tokens
