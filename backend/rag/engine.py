import re
import time
import logging
import statistics
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

logger = logging.getLogger("chatbot.rag.engine")


# ─── In-process latency ring-buffer (last 1000 calls) ─────────────────────────
_latency_history: Dict[str, List[float]] = {
    "total_ms": [],
    "retrieval_ms": [],
    "rerank_ms": [],
    "validation_ms": [],
    "llm_ms": [],
}
_MAX_HISTORY = 1000


def _record(key: str, value_ms: float) -> None:
    buf = _latency_history[key]
    buf.append(value_ms)
    if len(buf) > _MAX_HISTORY:
        buf.pop(0)


def get_latency_percentiles() -> Dict[str, Dict[str, float]]:
    """
    Returns P50 / P95 / P99 for each pipeline stage.
    Useful for the /admin/metrics endpoint or Prometheus scraping.
    """
    result = {}
    for stage, values in _latency_history.items():
        if not values:
            result[stage] = {"p50": 0.0, "p95": 0.0, "p99": 0.0, "n": 0}
            continue
        s = sorted(values)
        n = len(s)
        result[stage] = {
            "p50": round(s[int(n * 0.50)], 2),
            "p95": round(s[min(int(n * 0.95), n - 1)], 2),
            "p99": round(s[min(int(n * 0.99), n - 1)], 2),
            "mean": round(statistics.mean(s), 2),
            "n": n,
        }
    return result


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

    Each pipeline stage is individually timed; latencies are stored in a
    ring-buffer and exposed via get_latency_percentiles().
    """

    def __init__(self):
        self.settings = get_settings()
        self.llm_provider = get_llm_provider()

    def process_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        preferred_language: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes the complete end-to-end RAG pipeline for a user message.

        Args:
            query: User's raw query text
            conversation_history: Prior turns in this conversation
            preferred_language: User's language preference override
            tenant_id: Tenant scope for vector search isolation (None = search all)

        Returns dict with: answer, sources, detected_language, language_display,
            script, confidence, evidence_level, conflicts, is_fallback,
            llm_status, generation_source, rewritten_query, latency_ms
        """
        t_total_start = time.perf_counter()

        # ── Stage 1: Query Normalization & Language Understanding ─────────────
        q_proc = process_and_rewrite_query(
            query=query,
            conversation_history=conversation_history,
            user_preference=preferred_language,
        )

        search_query = q_proc["search_query"]
        lang_info = q_proc["language_info"]
        target_lang = lang_info["effective_language"]

        # ── Stage 2: Hybrid Retrieval ─────────────────────────────────────────
        t_retrieval_start = time.perf_counter()

        # 2a. Multilingual Vector Search (scoped to tenant)
        vector_candidates = vector_search(
            query=search_query,
            top_k=self.settings.vector_top_k,
            tenant_id=tenant_id,
        )

        # 2b. Multilingual BM25 Search (scoped to tenant and active status)
        bm25_filters = {"status": "active"}
        if tenant_id:
            bm25_filters["tenant_id"] = tenant_id
        bm25_idx = get_bm25_index()
        bm25_candidates = bm25_idx.search(
            query=search_query,
            top_k=self.settings.bm25_top_k,
            filters=bm25_filters,
        )

        # 2c. Reciprocal Rank Fusion
        fused_candidates = reciprocal_rank_fusion(
            vector_results=vector_candidates,
            bm25_results=bm25_candidates,
            top_k=self.settings.final_top_k * 2,
        )

        retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000
        _record("retrieval_ms", retrieval_ms)

        # ── Stage 2d: Reranking ───────────────────────────────────────────────
        t_rerank_start = time.perf_counter()
        final_sources = rerank_candidates(
            query=search_query,
            candidates=fused_candidates,
            top_k=self.settings.final_top_k,
        )
        rerank_ms = (time.perf_counter() - t_rerank_start) * 1000
        _record("rerank_ms", rerank_ms)

        # ── Stage 3: Evidence Validation ──────────────────────────────────────
        t_validation_start = time.perf_counter()
        is_sufficient, evidence_score, evidence_level, fallback_msg, conflicts = validate_evidence(
            sources=final_sources,
            target_language=target_lang,
            query=query,
        )
        validation_ms = (time.perf_counter() - t_validation_start) * 1000
        _record("validation_ms", validation_ms)

        # ── Insufficient evidence early exit ──────────────────────────────────
        if not is_sufficient:
            total_ms = (time.perf_counter() - t_total_start) * 1000
            _record("total_ms", total_ms)
            _record("llm_ms", 0.0)
            logger.info(
                "RAG pipeline: insufficient evidence — deterministic fallback",
                extra={
                    "stage": "fallback",
                    "retrieval_ms": round(retrieval_ms, 2),
                    "validation_ms": round(validation_ms, 2),
                    "total_ms": round(total_ms, 2),
                    "tenant_id": tenant_id,
                },
            )
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
                "llm_status": "NOT_INVOKED",
                "generation_source": "deterministic_fallback",
                "rewritten_query": search_query if q_proc["is_follow_up"] else None,
                "latency_ms": {
                    "retrieval": round(retrieval_ms, 2),
                    "rerank": round(rerank_ms, 2),
                    "validation": round(validation_ms, 2),
                    "llm": 0.0,
                    "total": round(total_ms, 2),
                },
            }

        # ── Stage 4: Prompt Construction ──────────────────────────────────────
        prompt = build_generation_prompt(
            query=query,
            sources=final_sources,
            conversation_history=conversation_history or [],
            target_language=target_lang,
        )

        # ── Stage 5: LLM Generation ───────────────────────────────────────────
        t_llm_start = time.perf_counter()
        gen_result = self.llm_provider.generate(
            prompt=prompt,
            system_prompt=BASE_SYSTEM_INSTRUCTION,
        )
        llm_ms = (time.perf_counter() - t_llm_start) * 1000
        _record("llm_ms", llm_ms)

        raw_answer = gen_result.text if hasattr(gen_result, "text") else str(gen_result)
        llm_status = gen_result.status if hasattr(gen_result, "status") else "LLM_SUCCESS"

        provider_name = getattr(self.settings, "llm_provider", "groq")
        if llm_status == "LLM_SUCCESS" and raw_answer:
            if "FALLBACK:" in raw_answer:
                clean_fb = raw_answer.replace("FALLBACK:", "").strip()
                answer = clean_fb if clean_fb else FALLBACK_MESSAGES.get(target_lang, FALLBACK_MESSAGES["en"])
                is_fallback = True
                llm_status = "LLM_FALLBACK"
                generation_source = provider_name
                return_sources = []
            else:
                answer = raw_answer
                is_fallback = False
                generation_source = provider_name
                return_sources = final_sources
        else:
            # Rate limit / timeout / provider failure — degrade gracefully with grounded synthesis
            if final_sources and is_sufficient:
                answer = self._synthesize_grounded_fallback(final_sources, query, target_lang)
                is_fallback = False
                generation_source = "evidence_fallback"
                return_sources = final_sources
            else:
                answer = FALLBACK_MESSAGES.get(target_lang, FALLBACK_MESSAGES["en"])
                is_fallback = True
                generation_source = "deterministic_fallback"
                return_sources = []

        # Append transparent conflict advisory if version discrepancies detected
        if conflicts and not is_fallback:
            conflict_notice = f"\n\n*(Note: {conflicts[0]} - Please verify with the latest official gazette.)*"
            answer += conflict_notice

        total_ms = (time.perf_counter() - t_total_start) * 1000
        _record("total_ms", total_ms)

        logger.info(
            "RAG pipeline complete",
            extra={
                "stage": "complete",
                "retrieval_ms": round(retrieval_ms, 2),
                "rerank_ms": round(rerank_ms, 2),
                "validation_ms": round(validation_ms, 2),
                "llm_ms": round(llm_ms, 2),
                "total_ms": round(total_ms, 2),
                "llm_status": llm_status,
                "evidence_level": evidence_level,
                "is_fallback": is_fallback,
                "tenant_id": tenant_id,
            },
        )

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
            "llm_status": llm_status,
            "generation_source": generation_source,
            "rewritten_query": search_query if q_proc["is_follow_up"] else None,
            "latency_ms": {
                "retrieval": round(retrieval_ms, 2),
                "rerank": round(rerank_ms, 2),
                "validation": round(validation_ms, 2),
                "llm": round(llm_ms, 2),
                "total": round(total_ms, 2),
            },
        }

    def _synthesize_grounded_fallback(
        self,
        sources: List[Dict[str, Any]],
        query: str,
        target_language: str
    ) -> str:
        """
        Synthesizes a structured, hallucination-free factual answer directly from validated
        evidence sources when the cloud LLM is rate-limited, times out, or is offline.
        Includes authoritative framing, key sentence extraction, and formal citations.
        """
        if not sources:
            return FALLBACK_MESSAGES.get(target_language, FALLBACK_MESSAGES["en"])

        lead_doc = sources[0]
        title = lead_doc.get("document_title") or lead_doc.get("title", "Official Policy")
        section = lead_doc.get("section", "Guidelines")
        page = lead_doc.get("page", 1)
        raw_text = lead_doc.get("text", "").strip()

        # Extract the most salient sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', raw_text) if s.strip()]
        body_text = " ".join(sentences[:3]) if sentences else raw_text[:350]

        # Multilingual attribution headers
        headers = {
            "en": f"According to official records for **{title}** ({section}):",
            "hi": f"**{title}** ({section}) के आधिकारिक अभिलेखों के अनुसार:",
            "hi-en": f"**{title}** ({section}) ke official records ke mutabiq:",
            "or": f"**{title}** ({section}) ର ସରକାରୀ ଅଭିଲେଖ ଅନୁଯାୟୀ:"
        }
        header = headers.get(target_language, headers["en"])

        return f"{header}\n\n{body_text}\n\n[Source: {title}, Page {page}]"

    # Aliases for interface convenience
    answer_query = process_query
    query = process_query


# ─── Singleton RAG engine instance ────────────────────────────────────────────
_engine_instance: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RAGEngine()
    return _engine_instance
