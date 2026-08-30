import math
from typing import List, Dict, Any, Optional
from collections import Counter
from backend.language.normalizer import tokenize_multilingual

class MultilingualBM25Index:
    """
    Okapi BM25 Index with full multilingual tokenization support
    (Devanagari, Odia, Latin Hinglish, English).
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []
        self.doc_tokens: List[List[str]] = []
        self.documents: List[Dict[str, Any]] = []

    def build_index(self, documents: List[Dict[str, Any]]):
        """
        Builds or rebuilds BM25 index from a list of document dicts.
        Each doc dict must contain 'text' and other metadata.
        """
        self.documents = documents
        self.corpus_size = len(documents)
        self.doc_tokens = []
        self.doc_len = []
        self.doc_freqs = Counter()

        if self.corpus_size == 0:
            self.avgdl = 0.0
            self.idf = {}
            return

        total_length = 0
        for doc in documents:
            text = doc.get("text", "")
            tokens = tokenize_multilingual(text)
            self.doc_tokens.append(tokens)
            l = len(tokens)
            self.doc_len.append(l)
            total_length += l
            
            # Count unique tokens in document for document frequency
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1

        self.avgdl = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Calculate standard Robertson-Spärck Jones IDF
        self.idf = {}
        for token, freq in self.doc_freqs.items():
            # Add 0.5 smoothing
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Searches the BM25 index with a query and optional metadata filters.
        Returns top-K document dicts with attached 'bm25_score'.
        """
        if self.corpus_size == 0 or not query:
            return []

        query_tokens = tokenize_multilingual(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.corpus_size

        for i, doc_toks in enumerate(self.doc_tokens):
            doc = self.documents[i]
            
            # Apply metadata filters if specified
            if filters:
                match = True
                for k, v in filters.items():
                    if doc.get(k) != v:
                        match = False
                        break
                if not match:
                    scores[i] = -1.0
                    continue

            # Calculate BM25 score
            tok_counter = Counter(doc_toks)
            doc_l = self.doc_len[i]
            score = 0.0

            for q_tok in query_tokens:
                if q_tok in tok_counter:
                    tf = tok_counter[q_tok]
                    idf = self.idf.get(q_tok, 0.1)
                    numerator = idf * tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_l / max(1.0, self.avgdl)))
                    score += (numerator / denominator)

            scores[i] = score

        # Rank documents
        ranked_indices = [idx for idx in range(self.corpus_size) if scores[idx] > 0]
        ranked_indices.sort(key=lambda idx: scores[idx], reverse=True)

        results = []
        max_score = max([scores[idx] for idx in ranked_indices], default=1.0)
        
        for idx in ranked_indices[:top_k]:
            doc_copy = dict(self.documents[idx])
            raw_score = scores[idx]
            # Soft monotonic normalization: raw_score / (raw_score + 5.0) prevents inflating single-word noise
            norm_score = min(1.0, raw_score / (raw_score + 5.0)) if raw_score > 0 else 0.0
            doc_copy["bm25_score"] = norm_score
            results.append(doc_copy)

        return results

    # Alias for method name compatibility
    index_documents = build_index

# Singleton index instance
_global_bm25_index: Optional[MultilingualBM25Index] = None

def get_bm25_index() -> MultilingualBM25Index:
    global _global_bm25_index
    if _global_bm25_index is None:
        _global_bm25_index = MultilingualBM25Index()
    return _global_bm25_index
