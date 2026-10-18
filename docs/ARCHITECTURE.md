# System Architecture & Active Pipeline Specification

## 1. Architectural Overview

The **Language Agnostic Chatbot** is a production-hardened, multi-layer Retrieval-Augmented Generation (RAG) system specifically designed for cross-lingual citizen queries over government welfare schemes, policies, and official documentation.

```
                      ┌───────────────────────────────┐
                      │    React 18 SPA Frontend      │
                      │ (Login · ChatUI · AdminPanel) │
                      └───────────────┬───────────────┘
                                      │ REST API (Bearer JWT)
                                      ▼
                      ┌───────────────────────────────┐
                      │    FastAPI Application Core   │
                      │  (CORS · Auth · Rate Limits)  │
                      └───────┬───────────────┬───────┘
                              │               │
                 Admin Routes │               │ Chat Routes
                              ▼               ▼
                 ┌───────────────────┐  ┌───────────────────────────────┐
                 │ Document Pipeline │  │          RAG Engine           │
                 │ (PyMuPDF · SHA256 │  │ (Detection · Hybrid Retrieval │
                 │  Section Chunking │  │  Fusion · Validation · LLM)   │
                 │  Versioning Store)│  └───────────────┬───────────────┘
                 └─────────┬─────────┘                  │
                           │                            │
                           ▼                            ▼
              ┌──────────────────────────┐   ┌─────────────────────────┐
              │     Vector Database      │   │     Sparse BM25 Index   │
              │  ChromaDB (Cosine HNSW)  │   │ Multilingual Okapi BM25 │
              │ (status == 'active' only)│   │ (active documents only) │
              └──────────────────────────┘   └─────────────────────────┘
```

---

## 2. Active Query Pipeline (Step-by-Step)

When a citizen submits a query via `POST /api/v1/chat`:

1. **Authentication & Session Injection:**
   - The request Bearer token is verified by `backend/auth/jwt.py`.
   - The user session is injected via FastAPI's `Depends(get_current_user)`.
   - The raw user query is persisted immutably in SQLite / PostgreSQL.

2. **Language Understanding & Script Distribution:**
   - Module: `backend/language/detector.py`
   - Detects character frequencies across scripts:
     - **Odia:** `[\u0B00-\u0B7F]` density $\ge 20\%$ $\rightarrow$ `or` (Odia script).
     - **Devanagari (Hindi):** `[\u0900-\u097F]` density $\ge 20\%$ $\rightarrow$ `hi` (Devanagari script).
     - **Latin:** Differentiates English (`en`) from Hinglish (`hi-en`) using a 50-word grammatical particle dictionary (`kya`, `hai`, `milega`, `dastavez`) and Hindi verb suffix heuristics (`-ega`, `-engi`, `-kar`).
     - **Mixed:** Flags multi-script inputs and applies dominant-script fallback.

3. **Unicode Normalization & Contextual Rewriting:**
   - Module: `backend/language/normalizer.py` & `backend/rag/query_processor.py`
   - Unicode NFKC normalization flattens character compositions and standardizes whitespace.
   - Evaluates conversation history (previous 4 turns): if referential pronouns ("it", "ye", "ଏହି") are used, the target scheme entity is extracted from previous turns and appended to produce `search_query`.

4. **Hybrid Retrieval (Dense + Sparse):**
   - **Dense Semantic Retrieval:** `backend/rag/vector_store.py`
     - Uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384-dimensional embeddings).
     - Queries ChromaDB HNSW cosine index filtering strictly on `status == "active"`.
     - *Offline Fallback:* If HuggingFace neural embedding models are unavailable, automatically falls back to lexical retrieval.
   - **Sparse Lexical Retrieval:** `backend/rag/bm25.py`
     - Uses custom `MultilingualBM25Index` with Robertson-Spärck Jones IDF variation.
     - Tokenizes across Devanagari, Odia, Latin scripts.
     - Employs soft monotonic normalization $\frac{\text{raw}}{\text{raw} + 5.0}$ to avoid inflating single-term documents.

5. **Reciprocal Rank Fusion (RRF):**
   - Module: `backend/rag/fusion.py`
   - Merges dense and sparse rankings using weighted reciprocal rank fusion ($k=60$):
     $$\text{RRF}(d) = 0.65 \cdot \frac{1}{60 + r_{\text{vector}}(d)} + 0.35 \cdot \frac{1}{60 + r_{\text{bm25}}(d)}$$
   - Computes unified confidence score combining semantic similarity and lexical overlap.

6. **Semantic-Lexical Reranking:**
   - Module: `backend/rag/reranker.py`
   - Active reranker: `SemanticLexicalReranker`
   - Evaluates query term coverage across body text and section headers.
   - Applies authority multipliers: official government gazettes ($1.05\times$), verified institutions ($1.02\times$), user uploads ($0.95\times$).

7. **Multi-Signal Evidence Validation:**
   - Module: `backend/rag/validator.py`
   - Computes composite evidence score:
     $$\text{Evidence} = 0.45 \cdot \text{MaxScore} + 0.25 \cdot \text{AvgScore} + 0.15 \cdot \text{Authority} + 0.15 \cdot \text{IntentCoverage}$$
   - **Guardrail Gate:** If `MaxScore < 0.25` or `Evidence < 0.25` or `IntentCoverage < 0.30`, the query is classified as `INSUFFICIENT`.
   - In `INSUFFICIENT` mode: Immediately returns a localized fallback message without contacting the LLM. Sources list is cleared to `[]`.
   - Detects numerical contradictions across versions (e.g. ₹5,000 vs ₹10,000) and appends advisory gazette notices.

8. **Prompt Construction & Generation:**
   - Module: `backend/rag/prompts.py` & `backend/rag/llm_provider.py`
   - Injects structured evidence blocks with source titles, sections, and pages.
   - Explicitly instructs Google Gemini on target script output:
     - Hindi: Devanagari script.
     - Hinglish: Latin script only (prohibits Devanagari mixing).
     - Odia: Odia script.
   - Provider: `GeminiProvider` with retry policy and structured error classification (`LLM_SUCCESS`, `LLM_TIMEOUT`, `LLM_RATE_LIMIT`, `LLM_AUTH_ERROR`, `LLM_PROVIDER_ERROR`).
   - If provider fails or hits quota limits, falls back to raw verified evidence text with `generation_source: "evidence_fallback"`.

---

## 3. Active Ingestion Pipeline

PDF Upload (`POST /api/v1/admin/documents`):
1. **Security Validation:**
   - File extension must be `.pdf`.
   - Content-Type must be `application/pdf`.
   - Magic binary bytes must be `%PDF`.
   - Size limit: $\le 25$ MB.
   - Corrupted/encrypted PDF check via PyMuPDF.
2. **Duplicate Deduplication:**
   - Computes SHA-256 checksum over file buffer.
   - Rejects identical uploads with `HTTP 409 Conflict`.
3. **Section-Aware Chunking:**
   - Extracts text and detects section titles (`Eligibility:`, `Benefits:`, `Documents:`, `ଯୋଗ୍ୟତା:`).
   - Chunks text to 500 words with 60-word overlap.
   - Attaches provenance metadata (`doc_id`, `version`, `department`, `authority_level`).
4. **Lifecycle & Version Isolation:**
   - Documents are uploaded with `status = "pending_approval"`.
   - On admin approval (`PATCH /api/v1/admin/documents/{id}`):
     - Status updates to `"active"`.
     - Older active versions of the same title/department are automatically archived (`status = "archived"`).
     - ChromaDB and BM25 indexes are synchronized with active documents only.

---

## 4. Consolidated Module Directory

| Active Component | Implementation File | Role |
| :--- | :--- | :--- |
| **API Entrypoint** | `backend/main.py` | FastAPI app, CORS, lifespan management |
| **Configuration** | `backend/config.py` | Environment settings and validation |
| **Auth & Security** | `backend/auth/jwt.py` | JWT token encode/decode and role policies |
| **Auth Routes** | `backend/auth/router.py` | Login, student registration, admin provisioning |
| **Database Models** | `backend/models/database.py` | SQLAlchemy ORM models |
| **Language Processing** | `backend/language/` | Detection & Unicode normalization |
| **RAG Orchestrator** | `backend/rag/engine.py` | End-to-end RAG workflow execution |
| **Vector Store** | `backend/rag/vector_store.py` | ChromaDB persistence and active filtering |
| **Sparse Index** | `backend/rag/bm25.py` | Multilingual Okapi BM25 |
| **Rank Fusion** | `backend/rag/fusion.py` | Weighted Reciprocal Rank Fusion |
| **Reranking** | `backend/rag/reranker.py` | Semantic-lexical & authority reranker |
| **Evidence Validation** | `backend/rag/validator.py` | Grounding and contradiction guardrails |
| **LLM Provider** | `backend/rag/llm_provider.py` | Google Gemini wrapper with fallback |
| **Ingestion Engine** | `backend/rag/ingestion.py` | PDF parsing, chunking, checksum, lifecycle |
| **Chat Endpoints** | `backend/routers/chat.py` | User chat, history, feedback |
| **Admin Endpoints** | `backend/routers/admin.py` | Document management & analytics |

*(Note: Legacy unmaintained files `chain.py`, `retrieval/retriever.py`, and `ingestion/pipeline.py` were removed in Phase 3 cleanup.)*
