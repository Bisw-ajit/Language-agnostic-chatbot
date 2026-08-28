import re
import langdetect

HINGLISH_KEYWORDS = {
    "kya", "hai", "hain", "ka", "ki", "ke", "liye", "kab", "kaise", "kahan", "chahiye",
    "mein", "me", "ko", "se", "par", "tha", "thi", "the", "hun", "ho", "nahi", "nahi",
    "bhi", "toh", "aur", "dastavez", "antim", "tithi", "chhatra", "patra", "rashi",
    "kare", "karna", "milega", "milta", "hoga", "sakte", "batao", "bataiye"
}

LANGUAGE_NAMES = {
    'en': 'ENGLISH',
    'hi': 'HINDI',
    'hi-en': 'HINGLISH',
    'or': 'ODIA',
    'unknown': 'ENGLISH'
}

def detect_language(text: str) -> str:
    if not text or not text.strip():
        return 'en'
        
    # Check for Devanagari script (Hindi)
    if re.search(r'[\u0900-\u097F]', text):
        return 'hi'
        
    # Check for Odia script
    if re.search(r'[\u0B00-\u0B7F]', text):
        return 'or'
        
    # Check for Hinglish (Latin script with Hindi words)
    words = [re.sub(r'[^\w]', '', w.lower()) for w in text.split()]
    hinglish_matches = sum(1 for w in words if w in HINGLISH_KEYWORDS)
    if hinglish_matches >= 1:
        return 'hi-en'
        
    # Standard langdetect fallback
    try:
        lang = langdetect.detect(text)
        if lang == 'hi':
            return 'hi'
        elif lang == 'or':
            return 'or'
    except Exception:
        pass
        
    return 'en'
