from typing import List, Dict, Any, Optional
from backend.config import get_settings
from backend.rag.query_processor import process_and_rewrite_query
from backend.rag.vector_store import vector_search
from backend.rag.bm25 import get_bm25_index
from backend.rag.fusion import reciprocal_rank_fusion
from backend.rag.reranker import rerank_candidates
from backend.rag.validator import validate_evidence
from backend.rag.prompts import build_generation_prompt, BASE_SYSTEM_INSTRUCTION, FALLBACK_MESSAGES
from backend.rag.llm_provider import get_llm_provider

class RAGEngine:
    """
    Master Modular RAG Engine orchestrating:
    - Multilingual Language Detection & Normalization
    - Contextual Query Rewriting
    - Hybrid Retrieval (Vector Search + Okapi BM25)
    - Reciprocal Rank Fusion & Reranking
    - Evidence Grounding Validation
    - Prompt Construction
    - Pluggable LLM Generation (Gemini)
    """
    def __init__(self):
        self.settings = get_settings()
        self.llm_provider = get_llm_provider()

    def process_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        preferred_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the complete end-to-end RAG pipeline for a user message.
        """
        # 1. Query Normalization & Language Understanding
        q_proc = process_and_rewrite_query(
            query=query,
            conversation_history=conversation_history,
            user_preference=preferred_language
        )
        
        search_query = q_proc["search_query"]
        lang_info = q_proc["language_info"]
        target_lang = lang_info["effective_language"]
        
        # 2. Hybrid Retrieval (Vector + BM25)
        # 2a. Multilingual Vector Search
        vector_candidates = vector_search(
            query=search_query,
            top_k=self.settings.vector_top_k
        )
        
        # 2b. Multilingual BM25 Search
        bm25_idx = get_bm25_index()
        bm25_candidates = bm25_idx.search(
            query=search_query,
            top_k=self.settings.bm25_top_k
        )
        
        # 2c. Reciprocal Rank Fusion
        fused_candidates = reciprocal_rank_fusion(
            vector_results=vector_candidates,
            bm25_results=bm25_candidates,
            top_k=self.settings.final_top_k * 2
        )
        
        # 2d. Optional Reranking
        final_sources = rerank_candidates(
            query=search_query,
            candidates=fused_candidates,
            top_k=self.settings.final_top_k
        )
        
        # 3. Multi-Signal Evidence Validation & Grounding Check
        is_sufficient, evidence_score, evidence_level, fallback_msg, conflicts = validate_evidence(
            sources=final_sources,
            target_language=target_lang,
            query=query
        )
        
        if not is_sufficient:
            return {
                "answer": fallback_msg,
                "sources": [],
                "detected_language": lang_info["language"],
                "language_display": lang_info["display_name"],
                "script": lang_info["script"],
                "confidence": evidence_score,
                "evidence_level": evidence_level,
                "conflicts": conflicts,
                "is_fallback": True,
                "rewritten_query": search_query if q_proc["is_follow_up"] else None
            }
            
        # 4. Prompt Generation
        prompt = build_generation_prompt(
            query=query,
            sources=final_sources,
            conversation_history=conversation_history or [],
            target_language=target_lang
        )
        
        # 5. LLM Answer Generation
        try:
            raw_answer = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=BASE_SYSTEM_INSTRUCTION
            )
            
            if "FALLBACK:" in raw_answer:
                # LLM correctly determined context does not support the specific question
                clean_fb = raw_answer.replace("FALLBACK:", "").strip()
                answer = clean_fb if clean_fb else FALLBACK_MESSAGES.get(target_lang, FALLBACK_MESSAGES["en"])
                is_fallback = True
                return_sources = []
            else:
                answer = raw_answer
                is_fallback = False
                return_sources = final_sources
                
        except Exception as e:
            print(f"[RAGEngine] LLM Generation Exception (using verified evidence fallback): {e}")
            if final_sources and is_sufficient:
                primary_text = final_sources[0].get("text", "").strip()
                answer = f"{primary_text}"
                is_fallback = False
                return_sources = final_sources
            else:
                answer = FALLBACK_MESSAGES.get(target_lang, FALLBACK_MESSAGES["en"])
                is_fallback = True
                return_sources = []

        # If conflicting versions were detected across sources, append a transparent advisory notice
        if conflicts and not is_fallback:
            conflict_notice = f"\n\n*(Note: {conflicts[0]} - Please verify with the latest official gazette.)*"
            answer += conflict_notice

        return {
            "answer": answer,
            "sources": return_sources,
            "detected_language": lang_info["language"],
            "language_display": lang_info["display_name"],
            "script": lang_info["script"],
            "confidence": evidence_score,
            "evidence_level": evidence_level,
            "conflicts": conflicts,
            "is_fallback": is_fallback,
            "rewritten_query": search_query if q_proc["is_follow_up"] else None
        }

    # Aliases for interface convenience
    answer_query = process_query
    query = process_query

# Singleton RAG engine instance
_engine_instance: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RAGEngine()
    return _engine_instance
