# RAG Architecture & Retrieval Pipeline

## Overview
The Language Agnostic Chatbot implements a modular, hybrid Retrieval-Augmented Generation (RAG) architecture tailored for multilingual institutional knowledge bases.

```
User Query
    │
    ▼
[1. Query Processor & Language Detector]
    ├── Script analysis (Devanagari, Odia, Latin)
    ├── Language identification (en, hi, hi-en, or)
    └── Contextual follow-up coreference resolution
    │
    ├─── Split into parallel retrieval ────────────────┐
    │                                                   │
    ▼                                                   ▼
[2a. Vector Retrieval]                             [2b. BM25 Retrieval]
ChromaDB dense search                              Okapi BM25 sparse search
(paraphrase-multilingual-MiniLM-L12-v2)             with Odia stemmer & Hinglish normalizer
    │                                                   │
    └───────────────────┬───────────────────────────────┘
                        ▼
            [2c. Reciprocal Rank Fusion]
            Merge rankings: RRF score = Σ 1 / (60 + rank)
                        │
                        ▼
            [2d. Reranking Layer]
            Semantic-Lexical Reranker / Cross-Encoder
                        │
                        ▼
            [3. Evidence Grounding Validator]
            ├── Max & average relevance scores
            ├── Authority weighting (official vs upload)
            ├── Query intent dimension coverage
            └── Cross-version contradiction check
                        │
            ┌───────────┴───────────┐
            │ Sufficient            │ Insufficient (< 0.25)
            ▼                       ▼
    [4. Prompt Construction]    [Deterministic Fallback]
    Context blocks + citations  "Information not found in official records"
            │
            ▼
    [5. Pluggable LLM Generation]
    Gemini Provider (with retry & status taxonomy)
            │
            ▼
    Verified Answer with Citations & Latency Metrics
```

---

## 1. Hybrid Retrieval Strategy

### Dense Vector Retrieval
- **Embedding Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384-dimensional dense vectors).
- **Capabilities**: Captures deep cross-lingual semantic similarity across Odia, Hindi, Hinglish, and English without explicit translation.
- **Tenant Scope**: Embeddings are filtered by tenant ID metadata to prevent cross-organization document leakage.

### Sparse Lexical Retrieval (BM25)
- **Engine**: Okapi BM25 index built in memory and synchronized from active ChromaDB chunks at startup.
- **Tokenization**: Multilingual character and subword n-gram tokenization with language-specific normalizers (Odia suffixes and Hinglish phonetic forms).
- **Complementarity**: Excels at retrieving exact scheme names (e.g. "KALIA", "Biju Swasthya Kalyan"), acronyms, document identifiers, and section numbers that dense vectors sometimes blur.

### Reciprocal Rank Fusion (RRF)
Combines dense and sparse rank lists using standard RRF formula with constant $k = 60$:
$$\text{RRF Score}(d) = \sum_{m \in \{\text{vector}, \text{bm25}\}} \frac{1}{60 + \text{rank}_m(d)}$$

---

## 2. Reranking Layer

The system supports pluggable rerankers via `RERANKER_TYPE`:
1. **`semantic_lexical`** (Default): Fast, zero-dependency reranker computing a weighted combination of semantic embedding distance and token overlap.
2. **`cross_encoder`**: Uses `cross-encoder/ms-marco-MiniLM-L-6-v2` for cross-attention scoring between query and candidate text. Lazy-loaded with fallback to semantic-lexical if offline.
3. **`passthrough`**: Bypasses reranking for minimal latency testing.

---

## 3. Evidence Grounding & Anti-Hallucination

Before calling the LLM, candidate documents are evaluated by `backend/rag/validator.py`:
- **Composite Evidence Score**: Weighted blend of maximum score (0.45), average top-3 score (0.25), authority weighting (0.15), and intent coverage (0.15).
- **Threshold Guard**: If composite evidence score $< 0.25$ or max score $< \text{threshold}$, the system skips LLM generation and directly returns a localized fallback message.
- **Contradiction Detection**: Flags numerical monetary discrepancy between different policy versions (e.g. v1 ₹5,000 vs v2 ₹10,000) and appends a transparent advisory notice.
