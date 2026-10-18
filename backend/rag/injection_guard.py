"""
Phase 15: Prompt Injection Defense

Detects and neutralizes adversarial prompt injection attempts before
queries reach the RAG pipeline or LLM generation stage.

Attack patterns defended against:
  1. Role confusion ("ignore previous instructions", "you are now DAN")
  2. System prompt exfiltration ("repeat your instructions", "show your system prompt")
  3. Jailbreak sequences ("pretend you have no restrictions", "DAN mode")
  4. Direct instruction injection in user input
  5. Unicode homoglyph / zero-width character obfuscation
  6. Nested bracket injection attempting CDATA-style escapes
"""

import re
import logging
import unicodedata
from typing import Tuple

logger = logging.getLogger("chatbot.security.injection")

# ─── Attack signature patterns ─────────────────────────────────────────────────
# Each pattern: (compiled_regex, severity: "block" | "sanitize", label)
_INJECTION_RULES = [
    # Role override / jailbreak
    (re.compile(r"ignore\s+(?:all\s+)?(?:previous\s+|prior\s+|above\s+|system\s+)?instructions?", re.I), "block", "role_override"),
    (re.compile(r"you\s+are\s+now\s+(?:DAN|GPT|an?\s+AI\s+without\s+restrictions?)", re.I), "block", "jailbreak_dan"),
    (re.compile(r"pretend\s+(?:you\s+)?have\s+no\s+restrictions?", re.I), "block", "jailbreak_restrictions"),
    (re.compile(r"act\s+as\s+(?:if\s+you\s+(?:have\s+no|are\s+not)|an?\s+unrestricted)", re.I), "block", "jailbreak_act_as"),
    (re.compile(r"disregard\s+(?:all\s+)?(?:prior|previous|your|above|all)\s+(?:instructions?|rules?|guidelines?)", re.I), "block", "instruction_override"),
    # System prompt exfiltration
    (re.compile(r"(?:repeat|show(?:\s+me)?|print|output|reveal|tell\s+me|what\s+is)\s+(?:your\s+|the\s+)?(?:system\s+prompt|base\s+instructions?|initial\s+prompt|system\s+instructions?)", re.I), "block", "system_exfil"),
    (re.compile(r"what\s+(?:are|were)\s+(?:your|the)\s+(?:first|initial|original)\s+instructions?", re.I), "block", "system_exfil"),
    # Prompt boundary injection (trying to close a prompt template)
    (re.compile(r"[`]{3,}|<\|(?:im_start|im_end|system|user|assistant)\|>", re.I), "block", "template_boundary"),
    (re.compile(r"###\s*(?:SYSTEM|INSTRUCTION|OVERRIDE|HUMAN|ASSISTANT|\w+\s+(?:OVERRIDE|INSTRUCTION|PROMPT))\s*###", re.I), "block", "template_boundary"),
    # LLM mode switching
    (re.compile(r"(?:developer|jailbreak|god|sudo)\s*mode", re.I), "block", "mode_switch"),
    (re.compile(r"token\s+limit\s+bypass|context\s+window\s+exploit", re.I), "block", "exploit_attempt"),
    # Force output manipulation
    (re.compile(r"respond\s+only\s+with\s+(?:yes|no|ok|sure|done)\s+then", re.I), "sanitize", "output_manip"),
]

# Zero-width / homoglyph characters
_INVISIBLE_CHARS_RE = re.compile(
    r"[\u200b\u200c\u200d\u2060\ufeff\u00ad\u034f\u115f\u1160\u17b4\u17b5\u3164]"
)

# Max query length (characters). LLMs can be confused by extremely long inputs.
_MAX_QUERY_LENGTH = 2000


def _strip_invisible(text: str) -> str:
    """Remove zero-width and invisible Unicode characters."""
    return _INVISIBLE_CHARS_RE.sub("", text)


def _normalize_unicode(text: str) -> str:
    """NFKC-normalize to collapse homoglyph substitutions."""
    return unicodedata.normalize("NFKC", text)


def sanitize_query(query: str) -> Tuple[bool, str, str]:
    """
    Sanitize a user query against prompt injection attacks.

    Args:
        query: Raw user input string

    Returns:
        (is_safe: bool, sanitized_query: str, threat_label: str)
        - is_safe=False means the query was BLOCKED (do not process further)
        - is_safe=True means the query is safe (possibly sanitized)
        - threat_label: empty string if safe, otherwise the attack category
    """
    if not query or not query.strip():
        return True, query, ""

    # 1. Unicode normalization + invisible character handling
    # Evaluate both spaced variant (zero-width used as word separator) and stripped variant
    cleaned_spaced = _normalize_unicode(_INVISIBLE_CHARS_RE.sub(" ", query))
    cleaned_stripped = _normalize_unicode(_INVISIBLE_CHARS_RE.sub("", query))

    # 2. Length cap
    if len(cleaned_spaced) > _MAX_QUERY_LENGTH:
        logger.warning(
            "Query truncated (too long)",
            extra={"original_len": len(cleaned_spaced), "max_len": _MAX_QUERY_LENGTH},
        )
        cleaned_spaced = cleaned_spaced[:_MAX_QUERY_LENGTH]

    # 3. Pattern matching across both normalized views
    for pattern, action, label in _INJECTION_RULES:
        for candidate in (cleaned_spaced, cleaned_stripped):
            if pattern.search(candidate):
                logger.warning(
                    f"Prompt injection detected: [{label}] action={action}",
                    extra={"label": label, "action": action, "query_snippet": candidate[:120]},
                )
                if action == "block":
                    return False, cleaned_spaced, label
                # "sanitize" — remove the matched segment
                cleaned_spaced = pattern.sub("[REDACTED]", cleaned_spaced)

    return True, cleaned_spaced, ""


def get_injection_rejection_message(threat_label: str, language: str = "en") -> str:
    """Return a user-facing rejection message for a blocked query."""
    _MESSAGES = {
        "en": "I can only answer questions about government schemes and institutional services. Please ask a relevant question.",
        "hi": "मैं केवल सरकारी योजनाओं और संस्थागत सेवाओं के बारे में प्रश्नों का उत्तर दे सकता हूँ।",
        "hi-en": "Main sirf government schemes aur institutional services ke baare mein jawab de sakta hoon.",
        "or": "ମୁଁ କେବଳ ସରକାରୀ ଯୋଜନା ଏବଂ ଅନୁଷ୍ଠାନ ସେବା ସମ୍ପର୍କୀୟ ପ୍ରଶ୍ନର ଉତ୍ତର ଦେଇ ପାରିବି।",
    }
    return _MESSAGES.get(language, _MESSAGES["en"])
