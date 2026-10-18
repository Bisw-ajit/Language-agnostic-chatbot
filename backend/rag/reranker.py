import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.config import get_settings
from backend.language.normalizer import tokenize_multilingual

logger = logging.getLogger("rag.reranker")

class BaseReranker(ABC):
    """
    Abstract Base Class for candidate document rerankers.
    Evaluates query-document relevance after initial fusion retrieval.
    """
    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Reranks candidates and returns the top_k most relevant documents."""
        pass

class PassthroughReranker(BaseReranker):
    """
    Lightweight zero-overhead reranker used when reranking is disabled.
    Preserves existing RRF candidate order.
    """
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        return candidates[:top_k]

ENGLISH_STOPWORDS = {
    "what", "is", "the", "for", "to", "of", "in", "and", "a", "an", "on", "at", "by",
    "this", "that", "it", "with", "as", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "can", "could", "should", "would", "will",
    "you", "me", "my", "we", "our", "us", "i", "he", "him", "his", "she", "her"
}

class SemanticLexicalReranker(BaseReranker):
    """
    Cross-lingual lexical-semantic reranker evaluating query term coverage,
    section heading matches, and authority level weighting.
    """
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        raw_query_tokens = set(tokenize_multilingual(query))
        if not raw_query_tokens:
            return candidates[:top_k]

        # Filter stopwords so common function words do not inflate lexical overlap
        content_query_tokens = {t for t in raw_query_tokens if t not in ENGLISH_STOPWORDS and len(t) > 2}
        effective_query_tokens = content_query_tokens if content_query_tokens else raw_query_tokens

        # Check if query is in Indic script (Devanagari or Odia)
        is_cross_lingual = bool(re.search(r'[\u0900-\u097F\u0B00-\u0B7F]', query))

        reranked = []
        for doc in candidates:
            text = doc.get("text", "")
            section = doc.get("section", "")
            doc_tokens = set(tokenize_multilingual(text))
            section_tokens = set(tokenize_multilingual(section))
            
            # Query term coverage in body text & section header
            text_overlap = len(effective_query_tokens.intersection(doc_tokens)) / max(1, len(effective_query_tokens))
            section_overlap = len(effective_query_tokens.intersection(section_tokens)) / max(1, len(effective_query_tokens))

            # Authority weight boost
            authority = doc.get("authority_level", "official")
            auth_weight = 1.0
            if authority == "official":
                auth_weight = 1.05
            elif authority == "trusted":
                auth_weight = 1.02
            elif authority == "demo":
                auth_weight = 1.0
            elif authority == "user_uploaded":
                auth_weight = 0.95
            elif authority == "unknown":
                auth_weight = 0.90

            base_score = doc.get("score", 0.5)
            
            # For cross-lingual Indic queries, lexical surface overlap against English docs is naturally absent.
            # Preserve the dense semantic similarity without the 0.65 penalty.
            if is_cross_lingual:
                boosted_score = min(1.0, base_score * auth_weight)
            elif text_overlap > 0 or section_overlap > 0:
                boosted_score = min(1.0, (base_score * 0.65 + text_overlap * 0.22 + section_overlap * 0.13) * auth_weight)
            else:
                boosted_score = min(1.0, base_score * 0.65 * auth_weight)
            
            doc_copy = dict(doc)
            doc_copy["reranker_score"] = round(boosted_score, 3)
            doc_copy["score"] = round(boosted_score, 3)
            reranked.append(doc_copy)

        # Sort descending by final boosted score
        reranked.sort(key=lambda d: d.get("score", 0.0), reverse=True)
        return reranked[:top_k]

class CrossEncoderReranker(BaseReranker):
    """
    Deep Neural Cross-Encoder Reranker using Sentence-Transformers.
    Performs full joint self-attention over [query, candidate_text] pairs.
    Lazy-loads weights on first execution with graceful fallback if offline.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
        self._init_attempted = False
        self._fallback = SemanticLexicalReranker()

    def _init_model(self):
        if not self._init_attempted:
            self._init_attempted = True
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
                logger.info(f"[CrossEncoderReranker] Successfully loaded '{self.model_name}'")
            except Exception as e:
                logger.warning(f"[CrossEncoderReranker] Could not load '{self.model_name}' ({e}). Falling back to SemanticLexicalReranker.")
                self._model = None

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        self._init_model()
        if self._model is None:
            return self._fallback.rerank(query, candidates, top_k)

        try:
            pairs = [[query, c.get("text", "")] for c in candidates]
            scores = self._model.predict(pairs)
            
            reranked = []
            for doc, raw_score in zip(candidates, scores):
                # Sigmoid scaling for cross-encoder logits into 0.0 - 1.0 confidence
                import math
                norm_score = 1.0 / (1.0 + math.exp(-float(raw_score)))
                
                doc_copy = dict(doc)
                doc_copy["cross_encoder_raw"] = round(float(raw_score), 4)
                doc_copy["reranker_score"] = round(norm_score, 4)
                doc_copy["score"] = round(norm_score, 4)
                reranked.append(doc_copy)

            reranked.sort(key=lambda d: d.get("score", 0.0), reverse=True)
            return reranked[:top_k]
        except Exception as e:
            logger.warning(f"[CrossEncoderReranker] Prediction failed: {e}. Using fallback.")
            return self._fallback.rerank(query, candidates, top_k)

def get_reranker() -> BaseReranker:
    """Factory function returning the configured reranker instance."""
    settings = get_settings()
    if not settings.enable_reranker or settings.reranker_type == "passthrough":
        return PassthroughReranker()
    elif settings.reranker_type == "cross_encoder":
        return CrossEncoderReranker(model_name=settings.cross_encoder_model)
    return SemanticLexicalReranker()

def rerank_candidates(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Convenience helper delegating to the active Reranker interface."""
    reranker = get_reranker()
    return reranker.rerank(query, candidates, top_k)
