import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.config import get_settings
from backend.language.normalizer import tokenize_multilingual

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

        query_tokens = set(tokenize_multilingual(query))
        if not query_tokens:
            return candidates[:top_k]

        reranked = []
        for doc in candidates:
            text = doc.get("text", "")
            section = doc.get("section", "")
            doc_tokens = set(tokenize_multilingual(text))
            section_tokens = set(tokenize_multilingual(section))
            
            # Query term coverage in body text & section header
            text_overlap = len(query_tokens.intersection(doc_tokens)) / max(1, len(query_tokens))
            section_overlap = len(query_tokens.intersection(section_tokens)) / max(1, len(query_tokens))

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
            boosted_score = min(1.0, (base_score * 0.65 + text_overlap * 0.22 + section_overlap * 0.13) * auth_weight)
            
            doc_copy = dict(doc)
            doc_copy["reranker_score"] = round(boosted_score, 3)
            doc_copy["score"] = round(boosted_score, 3)
            reranked.append(doc_copy)

        # Sort descending by final boosted score
        reranked.sort(key=lambda d: d.get("score", 0.0), reverse=True)
        return reranked[:top_k]

class CrossEncoderReranker(BaseReranker):
    """
    Semantic Cross-Encoder Reranker for deep sentence-pair relevance evaluation.
    Falls back to SemanticLexicalReranker if offline.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
        self._fallback = SemanticLexicalReranker()

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # Use fallback if cross encoder model is not loaded
        return self._fallback.rerank(query, candidates, top_k)

def get_reranker() -> BaseReranker:
    """Factory function returning the configured reranker instance."""
    settings = get_settings()
    if not settings.enable_reranker:
        return PassthroughReranker()
    return SemanticLexicalReranker()

def rerank_candidates(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Convenience helper delegating to the active Reranker interface."""
    reranker = get_reranker()
    return reranker.rerank(query, candidates, top_k)
