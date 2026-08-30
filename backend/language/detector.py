import re
from typing import Dict, Any, Optional
import langdetect

HINGLISH_KEYWORDS = {
    "kya", "hai", "hain", "liye", "kab", "kaise", "kahan", "chahiye",
    "mein", "tha", "thi", "hun", "nahi", "nahin", "mat",
    "bhi", "toh", "aur", "dastavez", "antim", "tithi", "chhatra", "patra", "rashi",
    "kare", "karna", "milega", "milta", "hoga", "sakte", "batao", "bataiye", "mujhe",
    "iske", "uske", "kis", "kisko", "yojana", "yojna", "aavedan", "shuru", "patrata",
    "kaunse", "kitna", "kitni", "karega", "dijiye", "kripya", "karo", "apna", "apne",
    "baare", "paisa", "sarkari", "yaha", "waha", "kaun", "kyon", "kyun", "wala", "wali"
}

# Common Hindi verb suffixes in Latin script
HINGLISH_SUFFIXES = ("ega", "egi", "enge", "unga", "ungi", "oge", "iye", "kar", "karo", "raha", "rahi", "rahe", "wala", "wali")

LANGUAGE_NAMES = {
    'en': 'ENGLISH',
    'hi': 'HINDI',
    'hi-en': 'HINGLISH',
    'or': 'ODIA',
    'mixed': 'MIXED',
    'unknown': 'ENGLISH'
}

def detect_language_structured(text: str, user_preference: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns structured language detection data with multi-script & mixed-language support:
    {
        "language": "en" | "hi" | "hi-en" | "or" | "mixed",
        "confidence": float,
        "script": "latin" | "devanagari" | "odia" | "mixed",
        "display_name": "ENGLISH" | "HINDI" | "HINGLISH" | "ODIA" | "MIXED",
        "effective_language": str,
        "is_mixed": bool
    }
    """
    if not text or not text.strip():
        default_lang = user_preference or 'en'
        return {
            "language": default_lang,
            "confidence": 1.0,
            "script": "latin",
            "display_name": LANGUAGE_NAMES.get(default_lang, 'ENGLISH'),
            "effective_language": default_lang,
            "is_mixed": False
        }

    raw_text = text.strip()
    total_alpha = len(re.findall(r'[\w]', raw_text))
    if total_alpha == 0:
        default_lang = user_preference or 'en'
        return {
            "language": default_lang,
            "confidence": 0.5,
            "script": "latin",
            "display_name": LANGUAGE_NAMES.get(default_lang, 'ENGLISH'),
            "effective_language": default_lang,
            "is_mixed": False
        }

    # Count script character distributions
    odia_chars = len(re.findall(r'[\u0B00-\u0B7F]', raw_text))
    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', raw_text))
    latin_chars = len(re.findall(r'[a-zA-Z]', raw_text))

    odia_ratio = odia_chars / total_alpha
    dev_ratio = devanagari_chars / total_alpha
    latin_ratio = latin_chars / total_alpha

    # 1. Mixed Script / Multi-Language Check
    active_scripts = sum([1 for r in [odia_ratio, dev_ratio, latin_ratio] if r >= 0.15])
    if active_scripts >= 2:
        # Determine dominant script / effective fallback language
        if odia_ratio >= dev_ratio and odia_ratio >= latin_ratio:
            dominant_lang = "or"
        elif dev_ratio >= odia_ratio and dev_ratio >= latin_ratio:
            dominant_lang = "hi"
        else:
            dominant_lang = "hi-en"

        effective = user_preference if user_preference else dominant_lang
        return {
            "language": "mixed",
            "confidence": round(max(odia_ratio, dev_ratio, latin_ratio), 2),
            "script": "mixed",
            "display_name": "MIXED",
            "effective_language": effective,
            "is_mixed": True
        }

    # 2. Pure / Dominant Odia Script
    if odia_ratio >= 0.20:
        conf = min(0.99, max(0.70, odia_ratio + 0.25))
        detected = "or"
        effective = user_preference if user_preference else detected
        return {
            "language": detected,
            "confidence": round(conf, 2),
            "script": "odia",
            "display_name": LANGUAGE_NAMES.get(effective, 'ODIA'),
            "effective_language": effective,
            "is_mixed": False
        }

    # 3. Pure / Dominant Devanagari Script (Hindi)
    if dev_ratio >= 0.20:
        conf = min(0.99, max(0.70, dev_ratio + 0.25))
        detected = "hi"
        effective = user_preference if user_preference else detected
        return {
            "language": detected,
            "confidence": round(conf, 2),
            "script": "devanagari",
            "display_name": LANGUAGE_NAMES.get(effective, 'HINDI'),
            "effective_language": effective,
            "is_mixed": False
        }

    # 4. Latin Script: Differentiate Hinglish vs. English
    words = [re.sub(r'[^\w]', '', w.lower()) for w in raw_text.split() if w.strip()]
    if words:
        hinglish_hits = 0
        for w in words:
            if w in HINGLISH_KEYWORDS:
                hinglish_hits += 1
            elif any(w.endswith(suf) and len(w) > len(suf) + 2 for suf in HINGLISH_SUFFIXES):
                hinglish_hits += 1

        hinglish_ratio = hinglish_hits / len(words)
        if hinglish_hits >= 1:
            conf = min(0.95, max(0.65, hinglish_ratio * 1.4 + 0.45))
            detected = "hi-en"
            effective = user_preference if user_preference else detected
            return {
                "language": detected,
                "confidence": round(conf, 2),
                "script": "latin",
                "display_name": LANGUAGE_NAMES.get(effective, 'HINGLISH'),
                "effective_language": effective,
                "is_mixed": False
            }

    # 5. Standard Statistical Detector for English / Latin
    detected = 'en'
    conf = 0.88
    try:
        lang = langdetect.detect(raw_text)
        if lang in ['en', 'hi', 'or']:
            detected = lang
    except Exception:
        pass

    effective = user_preference if user_preference else detected
    return {
        "language": detected,
        "confidence": round(conf, 2),
        "script": "latin",
        "display_name": LANGUAGE_NAMES.get(effective, 'ENGLISH'),
        "effective_language": effective,
        "is_mixed": False
    }

def detect_language(text: str, user_preference: Optional[str] = None) -> str:
    """Helper returning string effective language code."""
    res = detect_language_structured(text, user_preference=user_preference)
    return res["effective_language"]

