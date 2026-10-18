# Repository Inventory & Production Audit Report

**Project**: Language Agnostic Chatbot (SIH25104)  
**Audit Date**: October 2026  
**Auditor**: Senior Software Engineer & Security Auditor  
**Branch**: `audit/production-readiness`  
**Status**: Production Verified & Hardened  

---

## 1. Executive Summary

This repository audit evaluated the entire codebase of **Language Agnostic Chatbot** across backend microservices, vector storage pipelines, frontend single-page application (SPA), test suites, configuration artifacts, and CI/CD assets. The audit established empirical baselines, identified disposable artifacts and untracked assets, removed confirmed security vulnerabilities, verified dependency completeness, and ensured complete GitHub and Render deployment readiness.

---

## 2. Repository Inventory

### 2.1 File & Directory Breakdown

| Directory / Path | Purpose | Files Count | Size / Footprint | GitHub Suitability |
|---|---|---|---|---|
| `backend/` | FastAPI application, RAG pipeline, Auth, Normalizer, Observability | 25 Python modules | ~220 KB source | ✅ Suitable (Essential Core) |
| `backend/seed_documents/` | Official Odisha welfare scheme sample PDFs & generators | 4 PDFs + 2 scripts | ~15 KB | ✅ Suitable (Tracked Seed Data) |
| `backend/alembic/` | Database migration scripts and version heads | 4 files | ~8 KB | ✅ Suitable (Database Migrations) |
| `frontend/` | React 18 + Vite SPA, CSS modules, Axios client | 12 files | ~340 KB source | ✅ Suitable (Essential Core) |
| `tests/` | Pytest & Unittest test suite (12 test modules) | 12 test files | ~75 KB | ✅ Suitable (Automated Verification) |
| `evaluation/` | Empirical benchmark datasets, evaluation runners, result JSONs | 11 files | ~320 KB | ✅ Suitable (Reproducible Benchmarks) |
| `docs/` | System architecture, security model, user stories, screenshots | 15 docs + images | ~2.5 MB | ✅ Suitable (Documentation & Evidence) |
| `data/` | Ingestion state (`corpus_manifest.csv`, `corpus_state.json`) | 2 state files | ~11 KB | ✅ Suitable (State files tracked) |
| `data/raw_pdfs/` | Downloaded bulk PDF cache from Odisha portals | 19 raw PDFs | ~55.2 MB | ⚠️ Excluded via `.gitignore` (Bulk storage) |
| `chroma_data/` | Local SQLite & binary index vector store cache | 3 files | ~28.4 MB | ⚠️ Excluded via `.gitignore` (Local Cache) |
| `chatbot.db` | Local SQLite operational database | 1 binary | ~196 KB | ⚠️ Excluded via `.gitignore` (Local DB) |
| `uploads/` | Local admin file upload directory | Directory | Empty/Local | ⚠️ Excluded via `.gitignore` (Local Uploads) |
| `node_modules/` & `venv/` | Node and Python virtual environments | Thousands | Hundreds of MB | ⚠️ Excluded via `.gitignore` |

---

## 3. Detailed Inventory Analysis

### 3.1 Empty Files & Empty Directories
- **Found**:
  - `backend/__init__.py`, `backend/routers/__init__.py`, `backend/auth/__init__.py`, `backend/contracts/__init__.py`, `backend/language/__init__.py`, `backend/models/__init__.py`, `backend/rag/__init__.py`.
  - `data/raw_pdfs/nonexistent_dept`: Generated dynamically during negative testing in `test_odisha_ingestion_system.py`.
- **Verdict & Action**: **Preserved**. Python `__init__.py` files are required for proper package discovery in Python 3.9+ environments and Docker packaging. Empty test output directories are ignored.

### 3.2 Duplicate & Near-Duplicate Code
- **Investigation**:
  - Legacy ingestion pipeline (`backend/ingestion/pipeline.py`), legacy retriever (`backend/retrieval/retriever.py`), and legacy chain (`backend/rag/chain.py`) had been removed during modernization.
  - Search across the entire codebase confirmed **zero references** to these legacy modules. All active code routes through `backend.rag.engine.RAGEngine`, `backend.rag.ingestion.process_document_ingestion`, and `backend.rag.vector_store`.
- **Action**: Confirmed deletions are clean.

### 3.3 Dependencies & Requirements Audit
- **Findings**:
  - `backend/requirements.txt` previously omitted `Pillow` and `requests`. While these happened to be installed transitively in some local environments, a fresh build on Render or GitHub Actions failed because `PIL.Image` is imported in `backend/rag/ingestion.py` and `requests` is imported in `backend/rag/odisha_corpus_manager.py`.
- **Action**: Added `Pillow>=10.0.0` and `requests>=2.31.0` to `backend/requirements.txt`.

### 3.4 Tracked Datasets & Large Binaries
- **Investigation**:
  - `data/raw_pdfs/` contains 19 downloaded PDFs totaling 55.2 MB (e.g. `mkuy_pdf.pdf` is 14 MB).
  - Tracking 55 MB of arbitrary scraped PDFs inside a GitHub git repository permanently inflates clone sizes.
  - Core seed documents (`bsky_health_policy.pdf`, `kalia_yojana_guidelines.pdf`, `madhu_babu_pension_scheme.pdf`, `odisha_scholarship_policy.pdf`) are only ~2.3 KB each and are preserved in `backend/seed_documents/`.
- **Action**: Added `data/raw_pdfs/` to `.gitignore`. Kept `data/corpus_manifest.csv` and `data/corpus_state.json` tracked to preserve complete corpus metadata and provenance.

### 3.5 Local Databases & Generated Artifacts
- **Investigation**:
  - `chatbot.db`, `chroma_data/`, `frontend/dist/`, `.pytest_cache/`, `.DS_Store` are local artifacts.
- **Action**: Verified `.gitignore` covers `*.db`, `*.sqlite3`, `chroma_data/`, `backend/chroma_data/`, `uploads/`, `backend/uploads/`, `data/raw_pdfs/`, `dist/`, `.DS_Store`, `.coverage`, `htmlcov/`, and `*.log`.

---

## 4. Applied Modifications Summary

| File | Change Description | Rationale |
|---|---|---|
| `backend/routers/chat.py` | Added prompt injection guard (`sanitize_query`) to `/api/v1/chat/stream` SSE endpoint | Closed critical bypass where streaming queries avoided injection validation |
| `backend/main.py` | Guarded `seed_demo_users()` so it only runs when `ENVIRONMENT != 'production'` | Prevented default hardcoded demo accounts from being created in production |
| `backend/routers/admin.py` | Replaced hardcoded `./uploads` with `settings.upload_dir` | Dynamic path resolution matching environment configuration |
| `backend/auth/router.py` | Replaced bare `except Exception: pass` with explicit error logging | Fixed Bandit B110 finding and improved debugging traceability |
| `backend/requirements.txt` | Added `Pillow>=10.0.0` and `requests>=2.31.0` | Fixed missing runtime dependencies for fresh environments |
| `backend/Dockerfile` | Updated start CMD to bind dynamically to `${PORT:-8000}` | Required for Render web service dynamic port routing |
| `.gitignore` | Added `data/raw_pdfs/`, `.coverage`, `htmlcov/`, `*.log` | Prevented large binaries and coverage data from polluting git |
| `tests/test_security_suite.py` | Added test cases for streaming prompt injection and unary injection | Regression protection for prompt injection guards |
| `render.yaml` | Created Render deployment blueprint | Automated one-click Render deployment |
| `.github/workflows/ci.yml` | Created GitHub Actions automated test & build workflow | CI/CD validation on every push and pull request |
| `LICENSE` | Created official MIT License | Formal open-source licensing matching README declaration |
| `SECURITY.md` | Created security policy & vulnerability disclosure policy | GitHub Community Standard compliance |
| `CONTRIBUTING.md` | Created contributing guide | Standard open-source guidance |

---

## 5. Remaining Risks & Recommendations

1. **Persistent Vector Storage on Render**:
   - Render Web Services use ephemeral local container filesystems. If deployed on the Free tier without a Persistent Disk, ChromaDB and SQLite will reset on service restart.
   - *Recommendation*: For persistent production, attach a Render Persistent Disk at `/var/data` or use Render Managed PostgreSQL with external object storage (AWS S3, Cloudflare R2, or Google Cloud Storage).
2. **LLM API Quota Management**:
   - Groq free tier has TPM (tokens per minute) rate limits. The implemented provider has a 60-second exponential cooldown and fallback to Gemini or grounded evidence synthesis, which gracefully mitigates quota exhaustion.
