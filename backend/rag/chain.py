import os
import google.generativeai as genai
from backend.config import get_settings
from backend.retrieval.retriever import retrieve
from backend.language.detector import detect_language, LANGUAGE_NAMES

settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)

def build_rag_response(query: str, conversation_history: list, k: int = 5) -> dict:
    detected_lang_code = detect_language(query)
    language_display = LANGUAGE_NAMES.get(detected_lang_code, "ENGLISH")
    
    # Retrieve sources
    sources = retrieve(query, k=k)
    
    confidence = 0.0
    if sources:
        # Confidence is highest retrieval score
        confidence = max(s['score'] for s in sources)
    
    is_fallback = False
    
    if not sources or confidence < settings.confidence_threshold:
        is_fallback = True
        
    context_text = "\n\n".join([f"Source ({s['source']}, pg {s['page']}):\n{s['text']}" for s in sources])
    
    system_prompt = (
        "You are a helpful institutional information desk assistant for a college/university.\n"
        "Instructions:\n"
        "1. Answer ONLY based on the provided Context from official documents.\n"
        "2. If the Context does not contain the answer, respond with exactly:\n"
        "'FALLBACK: I could not find reliable information about that in the available institutional knowledge base.'\n"
        "3. NEVER fabricate facts, deadlines, amounts, or eligibility criteria not present in the context.\n"
        "4. Respond in the same language or script as the user's question (Hindi in Devanagari script, Hinglish in Latin script, English in English, Odia in Odia).\n"
        "5. Keep the answer clear, helpful, and concise."
    )
    
    history_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in conversation_history[-3:]])
    
    full_prompt = f"{system_prompt}\n\nContext:\n{context_text}\n\nRecent History:\n{history_text}\n\nUser Question:\n{query}\n\nAssistant:"
    
    answer = "I could not find reliable information about that in the available institutional knowledge base."
    
    if not is_fallback:
        try:
            model = genai.GenerativeModel(settings.gemini_model)
            response = model.generate_content(full_prompt)
            generated_text = response.text.strip()
            if "FALLBACK:" in generated_text:
                is_fallback = True
            else:
                answer = generated_text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            is_fallback = True
    
    if is_fallback:
        answer = "I could not find reliable information about that in the available institutional knowledge base."
        return_sources = []
    else:
        return_sources = sources
    
    return {
        "answer": answer,
        "sources": return_sources,
        "detected_language": detected_lang_code,
        "confidence": confidence,
        "is_fallback": is_fallback,
        "language_display": language_display
    }
