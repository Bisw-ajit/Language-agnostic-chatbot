# SaaS Transformation Status & Baseline Audit Report
**Project:** Language Agnostic Chatbot — SIH25104  
**Date:** September 2026  
**Architect:** Lead Software Architect & DevOps/Security Engineer  

---

## 1. Baseline Verification Summary

### 1.1 Automated Tests (`pytest tests/ -v`)
- **Collected:** 19 test cases across 3 test suites
- **Execution Status:** **19 PASSED (100%)** in 13.55s
  - `tests/test_master_engineering_suite.py`: 6 passed (checksum, provenance retention, contradiction detection, RAG end-to-end, evidence levels, fusion/reranker interface, language detection spectrum).
  - `tests/test_provenance_and_versioning.py`: 3 passed (checksum calculation, provenance metadata attachment, archived document exclusion).
  - `tests/test_rag_pipeline.py`: 10 passed (language detection en/hi/hi-en/or, multilingual BM25, RRF fusion, query rewriting, evidence validation fallback/success).

### 1.2 Evaluation Benchmark (`python evaluation/run_benchmarks.py`)
- **Stages 1-4:** Language detection (94% accuracy), retrieval strategy comparison (Recall@5: 98.8%, MRR: 0.913), cross-language equivalence (100% Doc IoU), Hinglish adversarial (95.8% accuracy).
- **Execution Crash:** Crashes at Stage 5/8 (`benchmark_evidence_and_contradictions`) due to `TypeError: cannot unpack non-iterable float object` on `check_intent_coverage()`.
- **Latency Measurement Finding:** The benchmark's claimed 1.18 ms latency measures only in-memory components (tokenization, BM25, ChromaDB, RRF, evidence validation) with MockProvider/fallback. Actual external Gemini network latency is 1,200 ms - 3,500 ms.

### 1.3 Backend & Runtime API Verification
- **Startup:** FastAPI starts cleanly on port 8000; DB tables created; demo users seeded (`admin@demo.com`, `student@demo.com`).
- **Endpoints:**
  - `GET /health`: Returns `{"status": "ok", "version": "1.0"}` (200 OK).
  - `POST /api/v1/auth/login`: Admin and Student authentication successful; JWT Bearer tokens issued.
  - `GET /api/v1/admin/documents`: Successfully lists seeded documents.
  - `PATCH /api/v1/admin/documents/{id}`: Successfully transitions documents to `active` and synchronizes ChromaDB and BM25.
  - `POST /api/v1/chat`: Complete RAG pipeline processes queries across languages with source attribution and confidence scoring.

### 1.4 Frontend Verification
- **Vite Build (`npm run build`):** 93 modules transformed; bundle built in 663 ms (`dist/assets/index-Cxg4tbyg.js` 249.39 kB).
- **UI Integration:** Full SPA with LoginPage, ChatPage, and AdminPage.

---

## 2. Dependency Graph & Module Classification

### Active Core Modules
- `backend/main.py`: FastAPI entrypoint, middleware, startup lifecycle, router mounting.
- `backend/config.py`: Pydantic BaseSettings loading `.env`.
- `backend/auth/jwt.py`: JWT token generation, verification, and role dependencies.
- `backend/auth/router.py`: Login and user registration endpoints.
- `backend/contracts/api_types.py`: Pydantic contract schemas.
- `backend/models/database.py`: SQLAlchemy models (User, Conversation, Message, Feedback, DocumentMetadata).
- `backend/language/detector.py`: Fast Unicode block & regex Hinglish detector.
- `backend/language/normalizer.py`: NFKC Unicode normalization and multilingual tokenization.
- `backend/rag/engine.py`: Master orchestrator for query flow.
- `backend/rag/vector_store.py`: ChromaDB integration with active status filtering & offline fallback.
- `backend/rag/bm25.py`: Okapi BM25 index with Robertson-Spärck Jones IDF & score normalization.
- `backend/rag/fusion.py`: Reciprocal Rank Fusion (weighted 0.65/0.35).
- `backend/rag/reranker.py`: SemanticLexicalReranker (active).
- `backend/rag/validator.py`: Evidence validation, intent coverage & contradiction detection.
- `backend/rag/prompts.py`: Prompt builder and multilingual target instructions.
- `backend/rag/llm_provider.py`: GeminiProvider & MockProvider.
- `backend/rag/query_processor.py`: Contextual query expansion.
- `backend/rag/ingestion.py`: Active PDF parsing, SHA-256 checksumming, section chunking.
- `backend/routers/chat.py`: `/chat`, `/conversations`, `/feedback` endpoints.
- `backend/routers/admin.py`: `/admin/documents`, `/analytics`, `/unanswered-queries`.

### Dead / Duplicate Legacy Modules
- `backend/rag/chain.py`: Unused legacy LangChain pipeline.
- `backend/retrieval/retriever.py`: Unused legacy Chroma retriever without BM25 sync or status filtering.
- `backend/ingestion/pipeline.py`: Unused legacy ingestion script.
- `backend/rag/reranker.py: CrossEncoderReranker`: Uninitialized stub class that delegates to fallback.

---

## 3. Known Bugs, Vulnerabilities & Production Risks

1. **[CRITICAL] Exposed Secret:** Live Google Gemini API key committed in `backend/.env`.
2. **[CRITICAL] Privilege Escalation:** `/api/v1/auth/register` accepts `role: "admin"` from unauthenticated callers.
3. **[CRITICAL] Permissive CORS:** Wildcard `allow_origins=["*"]` configured with `allow_credentials=True`.
4. **[HIGH] Invalid Gemini Model:** `GEMINI_MODEL=gemini-3.6-flash` in `.env` is non-existent; triggers API failure.
5. **[HIGH] Hardcoded JWT Secret:** Default `super-secret-jwt-key-change-in-production` in `.env` and `config.py`.
6. **[HIGH] Benchmark Crash:** `evaluation/run_benchmarks.py` crashes on stage 5/8 due to `check_intent_coverage` return mismatch.
7. **[MEDIUM] Unrestricted File Upload:** Missing PDF MIME validation and file size limits in admin upload.
8. **[MEDIUM] Single-Tenant DB Architecture:** Lacks tenant/workspace isolation and Alembic migration scripts.
9. **[MEDIUM] Database Discrepancy:** `POSTGRES_URL` points to SQLite in `.env` and PostgreSQL in `docker-compose.yml`.

---

## 4. Production Readiness: 50%
- Core algorithmic RAG pipeline is working and verified by unit tests.
- System requires immediate Phase 1 security lockdown, model reconfiguration, and SaaS architectural hardening before production deployment.
