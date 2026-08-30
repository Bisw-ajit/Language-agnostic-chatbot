import re
import unicodedata
from typing import List

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
    
    # Replace weird invisible characters and tabs with spaces
    text = re.sub(r'[\r\n\t]+', ' ', text)
    
    # Strip excessive spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def tokenize_multilingual(text: str) -> List[str]:
    """
    Tokenizes text across English, Hindi, Hinglish, and Odia.
    Splits on punctuation and whitespace, preserving unicode words and numbers.
    """
    normalized = normalize_text(text).lower()
    # Match any alphanumeric sequence including unicode scripts (\w matches unicode letters/digits)
    tokens = re.findall(r'[\w\u0900-\u097F\u0B00-\u0B7F]+', normalized)
    return tokens
