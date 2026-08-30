from typing import List, Dict, Any

FALLBACK_MESSAGES = {
    "en": "I could not find reliable information about that in the available official institutional knowledge base.",
    "hi": "मुझे उपलब्ध आधिकारिक ज्ञानकोष में इसके बारे में विश्वसनीय जानकारी नहीं मिली।",
    "hi-en": "Mujhe official institutional knowledge base mein iske baare mein reliable information nahi mili.",
    "or": "ଉପଲବ୍ଧ ସରକାରୀ ଜ୍ଞାନକୋଷରେ ଏହା ବିଷୟରେ ନିର୍ଭରଯୋଗ୍ୟ ସୂଚନା ମିଳିଲା ନାହିଁ।"
}

PROMPT_VERSION = "2.0.0"

BASE_SYSTEM_INSTRUCTION = """You are the official Institutional Information Desk Assistant for Citizen Services & Government Schemes.

CRITICAL NON-NEGOTIABLE RULES:
1. Grounding First: Answer ONLY and EXCLUSIVELY based on the provided Context from official documents.
2. Anti-Hallucination: Never fabricate facts, dates, amounts, deadlines, eligibility criteria, phone numbers, or application procedures not present in the context.
3. Fallback Trigger: If the Context does not contain sufficient facts to answer the question accurately, respond with EXACTLY the word 'FALLBACK:' followed by a helpful brief statement in the target language explaining that official records do not contain this information.
4. Multilingual Response: You MUST respond in the EXACT language requested:
   - English: Clear, professional English.
   - Hindi (hi): Fluent Hindi in Devanagari script (हिन्दी).
   - Hinglish (hi-en): Natural conversational Hinglish in Latin script (e.g. "Is yojana ke liye aapko..."). Do NOT use Devanagari when Hinglish is requested.
   - Odia (or): Fluent, grammatically correct Odia in Odia script (ଓଡ଼ିଆ).
5. Exact Figures: Preserve all numerical values, monetary amounts (e.g. ₹5,000, $5000), percentages, GPA/marks, and proper names exactly as stated in the context.
6. Conciseness: Provide structured bullet points where helpful, avoiding fluff or unnecessary disclaimers.
"""

def format_context_sources(sources: List[Dict[str, Any]]) -> str:
    """Formats retrieved document chunks into clean context blocks with citations."""
    if not sources:
        return "NO CONTEXT AVAILABLE."
        
    context_blocks = []
    for idx, s in enumerate(sources, start=1):
        doc_name = s.get("document_title") or s.get("source", "Document")
        page = s.get("page", 1)
        section = s.get("section", "General")
        dept = s.get("department", "General")
        text = s.get("text", "").strip()
        
        block = f"[Source {idx} | Document: {doc_name} | Section: {section} | Dept: {dept} | Page: {page}]\n{text}"
        context_blocks.append(block)
        
    return "\n\n".join(context_blocks)

def build_generation_prompt(
    query: str,
    sources: List[Dict[str, Any]],
    conversation_history: List[Dict[str, Any]],
    target_language: str
) -> str:
    """Constructs the prompt sent to the LLM."""
    context_str = format_context_sources(sources)
    
    # Format recent conversation history (last 3 turns)
    recent_history = conversation_history[-3:] if conversation_history else []
    history_str = "\n".join([f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in recent_history])
    if not history_str:
        history_str = "None (Start of conversation)"
        
    target_lang_instruction = {
        "en": "Target Output Language: ENGLISH",
        "hi": "Target Output Language: HINDI (in Devanagari script / हिन्दी)",
        "hi-en": "Target Output Language: HINGLISH (conversational Hindi written in Latin script)",
        "or": "Target Output Language: ODIA (in Odia script / ଓଡ଼ିଆ)"
    }.get(target_language, "Target Output Language: ENGLISH")

    prompt = f"""CONTEXT FROM OFFICIAL DOCUMENTS:
{context_str}

CONVERSATION HISTORY:
{history_str}

USER QUERY:
{query}

{target_lang_instruction}

ASSISTANT RESPONSE:"""
    return prompt
