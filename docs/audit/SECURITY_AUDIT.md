# Comprehensive Security Audit Report

**Project**: Language Agnostic Chatbot (SIH25104)  
**Audit Date**: October 2026  
**Security Classification**: Critical / High / Medium / Low  
**Branch**: `audit/production-readiness`  

---

## 1. Scope & Audit Methodology

The security audit evaluated the entire codebase, configuration files, Git commit history, and runtime environments using automated static analysis, dynamic testing, dependency auditing, and manual source review.

### Tools & Scanners Executed
- **Git Commit History Analysis**: Full history pattern matching for AWS, Groq, Gemini, OpenAI, and JWT keys across all commits and blobs.
- **Bandit v1.8.6**: Static application security testing (SAST) for Python security issues (CWE-703, CWE-259, CWE-22, etc.).
- **pip-audit v2.9.0**: CVE scan against the PyPI Advisory Database and CycloneDX SBOM.
- **Ruff v0.17.1**: AST-level code quality and syntax validation.
- **Pytest Security Suite**: 13 automated security regression tests (`tests/test_security_suite.py`).

---

## 2. Secrets & Credential Management Findings

### 2.1 Git History & Environment Scan
- **Check**: Scanned all commits (`git log -p --all -G <pattern>`) for Groq (`gsk_`), Google AI (`AIza`), OpenAI (`sk-`), and JWT signatures (`eyJ`).
- **Result**: **Clean (0 Exposed Secrets in Git History)**.
- **Finding**: In commit `dfad5184c7cf`, only `backend/.env.example` was tracked, containing safe placeholder tokens (`gsk_your_groq_api_key_here`, `your_gemini_api_key_here`).
- **Local `.env` Review**: A local `backend/.env` file exists for local development. It is strictly excluded by `.gitignore` lines 2–8 (`.env`, `backend/.env`, `**/.env`).
- **Verification Rule**: `.gitignore` comprehensively ignores all `.env*` files.

### 2.2 Production Secret Key Guard
- **Implementation**: Located in `backend/main.py:52–59`:
  ```python
  if settings.environment == "production":
      if settings.secret_key in [
          "super-secret-jwt-key-change-in-production", "secret", "change-this-in-production"
      ] or len(settings.secret_key) < 32:
          raise RuntimeError("FATAL: Insecure or default SECRET_KEY detected in production environment.")
  ```
- **Validation**: If `ENVIRONMENT=production` is set with a default or short key, the server process refuses to boot.

---

## 3. Vulnerability Findings & Remediation Log

### Finding SEC-01: Prompt Injection Guard Bypass on Streaming SSE Endpoint
- **Severity**: **High**
- **CWE**: CWE-20 (Improper Input Validation) / OWASP LLM01 (Prompt Injection)
- **Affected File**: `backend/routers/chat.py` (function `chat_stream`)
- **Evidence**:
  While the standard unary endpoint `/api/v1/chat` checked `sanitize_query(request.message)` and rejected jailbreaks and system prompt exfiltration, `/api/v1/chat/stream` took `request.message` directly and queued it into `engine.process_query()`. An attacker requesting `/api/v1/chat/stream` could bypass the guardrail completely.
- **Remediation Applied**:
  Added `sanitize_query(request.message)` check to `chat_stream()`. If flagged unsafe, the endpoint now records security metrics, logs an audit event, persists the rejection message, and emits SSE `stage: blocked` and `llm_status: BLOCKED_INJECTION` events without invoking the LLM.
- **Verification**: Added `test_chat_stream_prompt_injection_blocked()` to `tests/test_security_suite.py` which passes with 100% verification.

---

### Finding SEC-02: Automatic Hardcoded Demo User Seeding in Production
- **Severity**: **Medium**
- **CWE**: CWE-798 (Use of Hard-coded Credentials) / CWE-1188 (Insecure Default Initialization)
- **Affected File**: `backend/main.py` & `backend/models/database.py`
- **Evidence**:
  `lifespan()` unconditionally called `seed_demo_users()`, creating `admin@demo.com` with password `admin123` on every startup, even if `ENVIRONMENT=production`.
- **Remediation Applied**:
  Updated `lifespan()` in `backend/main.py` to check `if settings.environment != "production": seed_demo_users()`. In production environments, demo user seeding is completely bypassed.
- **Verification**: Verified via test suite and startup probe tests.

---

### Finding SEC-03: Hardcoded Upload Directory Inconsistency
- **Severity**: **Medium**
- **CWE**: CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)
- **Affected File**: `backend/routers/admin.py`
- **Evidence**:
  `UPLOAD_DIR = os.path.abspath("./uploads")` was hardcoded at module level, ignoring `settings.upload_dir` (`os.path.join(os.path.dirname(__file__), "uploads")`).
- **Remediation Applied**:
  Bound `UPLOAD_DIR` directly to `os.path.abspath(_settings.upload_dir)`. All uploaded files continue to pass through SHA-256 duplicate checking, filename sanitization (`re.sub(r'[^a-zA-Z0-9._-]', '_', basename)`), and directory confinement checks (`file_path.startswith(UPLOAD_DIR)`).

---

### Finding SEC-04: Bare `except Exception: pass` in Login Request Parsing
- **Severity**: **Low** (Code Hygiene / Observability)
- **CWE**: CWE-703 (Improper Check or Handling of Exceptional Conditions) / Bandit B110
- **Affected File**: `backend/auth/router.py:73, 80`
- **Evidence**:
  Bandit flagged `[B110:try_except_pass]` where JSON and Form body parsing silently swallowed all exceptions with `pass`.
- **Remediation Applied**:
  Introduced `logger = logging.getLogger("chatbot.auth.router")` and logged debug diagnostics `logger.debug("Failed to parse login body: %s", exc)`.

---

### Finding SEC-05: Missing Explicit Dependencies for PDF Ingestion and Corpus Sync
- **Severity**: **High (Availability)**
- **Affected File**: `backend/requirements.txt`
- **Evidence**:
  `Pillow` and `requests` were imported by `backend/rag/ingestion.py` and `backend/rag/odisha_corpus_manager.py`, but omitted from `requirements.txt`.
- **Remediation Applied**:
  Added `Pillow>=10.0.0` and `requests>=2.31.0` to `backend/requirements.txt`.

---

## 4. Static Analysis (Bandit) Detailed Results

- **Scan Target**: `backend/`
- **Total Lines Scanned**: 5,395
- **Confidence / Severity**:
  - High Severity: **0**
  - Medium Severity: **0**
  - Low Severity: 7 (3 in `odisha_corpus_manager.py` parsing checkpoints, 1 in `metrics.py` rusage fallback, 1 in `detector.py`, and 2 in `auth/router.py` token type parameter).

---

## 5. Dependency Vulnerability Audit (pip-audit)

Running `pip-audit -r backend/requirements.txt` evaluated installed dependencies against known CVEs.

### Vulnerability Summary Table

| Package | Installed Version | Advisory IDs | Remediation Recommendation |
|---|---|---|---|
| `starlette` | 0.49.3 | PYSEC-2026-161, PYSEC-2026-248 | Upgrade to `>=1.3.1` (transitive via FastAPI) |
| `python-multipart` | 0.0.20 | PYSEC-2026-1852, PYSEC-2026-3038 | Upgrade to `>=0.0.31` |
| `pymupdf` | 1.26.5 | PYSEC-2026-3001 | Upgrade to `>=1.26.7` |
| `requests` | 2.32.5 | PYSEC-2026-2275 | Upgrade to `>=2.33.0` |
| `urllib3` | 2.6.3 | PYSEC-2026-141, PYSEC-2026-4177 | Upgrade to `>=2.8.0` |
| `python-jose` | 3.5.0 | PYSEC-2026-4298 | Evaluate migration to `PyJWT` or `authlib` in future major release |

> [!NOTE]
> In production Render deployment, pip resolves latest compatible semantic versions satisfying `>=` constraints declared in `backend/requirements.txt`.

---

## 6. Access Control & Authorization (RBAC) Audit

| Role | Permissions | Enforcement Mechanism |
|---|---|---|
| **Anonymous** | Health checks (`/health`, `/readyz`), Swagger UI (`/docs`), Login (`/auth/login`), Student Registration (`/auth/register`) | Public endpoints |
| **Student** (`student`) | Send chat messages (`/chat`, `/chat/stream`), view own conversation history, submit feedback (`/feedback`) | `Depends(get_current_user)`, database tenant & user ID scoping |
| **Admin** (`admin`) | All Student permissions + Upload PDFs (`/admin/documents`), approve/reject documents, view analytics (`/admin/analytics`), view metrics | `Depends(require_role("admin", "super_admin"))` |
| **Super Admin** (`super_admin`) | All Admin permissions + Promote/Demote user roles (`/admin/users/{id}/role`), system-wide audit log access | `Depends(require_role("super_admin"))` |

### Multi-Tenancy Isolation
- Every database model (`User`, `Conversation`, `DocumentMetadata`, `AnalyticsDaily`) carries `tenant_id`.
- Vector search in `backend/rag/vector_store.py:vector_search()` enforces ChromaDB metadata filtering `{"tenant_id": tenant_id}` when multi-tenancy is active, preventing cross-tenant document exposure.
- Conversation access checks `Conversation.user_id == current_user.id` and `Conversation.tenant_id == user_tenant`.

---

## 7. RAG Security: Prompt Injection & Grounding

1. **Dual-View Unicode Normalization**:
   - Strips zero-width and invisible control characters (`\u200b`, `\u200c`, `\u200d`, `\ufeff`).
   - Normalizes text via Unicode NFKC to defeat homoglyph obfuscation.
2. **Signature & Boundary Detection**:
   - Blocks role confusion (`ignore previous instructions`, `DAN mode`).
   - Blocks prompt boundary tokens (`` ``` ``, `<|im_start|>`, `<|system|>`).
   - Blocks instruction exfiltration (`repeat system prompt`, `reveal initial instructions`).
3. **Empirical Measurement**:
   - 17 out of 17 injection attempts blocked in benchmark (`Block Rate = 1.0`).
   - 0 false positive rejections on genuine queries.

---

## 8. Residual Risks & Security Recommendations

1. **Rotate Credentials**:
   - Always supply `GROQ_API_KEY`, `GEMINI_API_KEY`, and a strong random `SECRET_KEY` (minimum 32 characters, generated with `openssl rand -hex 32`) via Render environment variables. Never commit `.env` to GitHub.
2. **CORS Origins Configuration**:
   - In production, set `CORS_ORIGINS` to the exact production frontend domain (e.g. `https://your-frontend.onrender.com`), not `*`.
3. **Rate Limiting**:
   - FastAPI middleware currently tracks request count in Prometheus. For high-volume production, place Cloudflare or a reverse-proxy rate limiter (e.g. Nginx `limit_req_zone` or Redis-backed SlowAPI) in front of the API.
