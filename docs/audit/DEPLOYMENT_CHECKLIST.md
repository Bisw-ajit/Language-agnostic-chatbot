# Render Deployment Checklist & Operations Guide

**Project**: Language Agnostic Chatbot (SIH25104)  
**Target Platform**: Render (Web Service + Static Site)  
**Document Status**: Production Verified  
**Date**: October 2026  

---

## 1. Render Architecture Architecture

```
                               ┌─────────────────────────────────┐
                               │     Render Static Site          │
                               │  (React 18 + Vite Frontend)     │
                               │  URL: https://frontend.onrender │
                               └────────────────┬────────────────┘
                                                │ HTTPS
                                                ▼
                               ┌─────────────────────────────────┐
                               │     Render Web Service          │
                               │   (FastAPI Backend API)         │
                               │  URL: https://backend.onrender  │
                               └────────┬───────────────┬────────┘
                                        │               │
                        Attached Disk   │               │ Render Managed DB
                              ▼         ▼               ▼
                 ┌───────────────────────────┐   ┌───────────────────────┐
                 │  Persistent Disk (/var)   │   │  PostgreSQL Database  │
                 │  /var/data/chroma_data    │   │  (Optional/Recommended│
                 │  /var/data/uploads        │   │   for Multi-Instance) │
                 └───────────────────────────┘   └───────────────────────┘
```

---

## 2. Service Configuration Matrix

### 2.1 Backend Web Service (Render)

| Configuration Field | Recommended Setting | Rationale |
|---|---|---|
| **Service Type** | Web Service | Long-running HTTP API server |
| **Environment** | Python 3 or Docker | Pre-configured `Dockerfile` provided |
| **Root Directory** | `.` | Root directory contains `alembic.ini` and `backend/` |
| **Build Command (Native Python)** | `pip install -r backend/requirements.txt` | Installs PyTorch, FastAPI, ChromaDB, etc. |
| **Start Command (Native Python)** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1` | Automatically binds to Render's allocated dynamic port |
| **Start Command (Docker)** | `CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]` | Configured inside `backend/Dockerfile` |
| **Health Check Path** | `/healthz` | Lightweight process probe for fast zero-downtime deployment |
| **Auto-Deploy** | Yes (on push to `main`) | Automated continuous delivery |
| **Instance Plan** | Starter ($7/mo) or Standard ($25/mo) | Memory requirements: ~900 MB peak RSS |

---

### 2.2 Frontend Static Site (Render)

| Configuration Field | Recommended Setting | Rationale |
|---|---|---|
| **Service Type** | Static Site | Zero server overhead for React SPA |
| **Root Directory** | `frontend` | Frontend directory |
| **Build Command** | `npm install && npm run build` | Produces production bundle in `dist/` |
| **Publish Directory** | `dist` | Destination of Vite build |
| **Routing Redirect / Rewrite** | `/* -> /index.html` (Status 200) | Required for React Router client-side routes |

---

## 3. Required Environment Variables

Configure these in the Render Dashboard under **Environment**:

| Variable Name | Required? | Example Value | Description |
|---|---|---|---|
| `ENVIRONMENT` | **Yes** | `production` | Enables JSON logging, security guards, disables demo seeding |
| `SECRET_KEY` | **Yes** | *(Generate 32-char hex)* | JWT signing secret. Must be $\ge 32$ chars. `openssl rand -hex 32` |
| `ALGORITHM` | **Yes** | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Token expiration in minutes (24 hours) |
| `GROQ_API_KEY` | **Yes** | `gsk_...` | Groq LLM API Key (https://console.groq.com/keys) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Primary Groq model ID |
| `LLM_PROVIDER` | No | `groq` | Primary LLM provider (`groq` or `gemini`) |
| `GEMINI_API_KEY` | Optional | `AIza...` | Optional fallback provider (Google AI Studio) |
| `GEMINI_MODEL` | No | `gemini-3.1-flash-lite` | Fallback model ID |
| `CORS_ORIGINS` | **Yes** | `https://your-frontend.onrender.com` | Exact frontend URL permitted to access the API |
| `POSTGRES_URL` | Optional | `postgresql://user:pass@host/db` | Render Postgres connection URL (defaults to SQLite if unset) |
| `CHROMA_PERSIST_DIR` | Optional | `/var/data/chroma_data` | Persistent disk mount path for vector DB |
| `UPLOAD_DIR` | Optional | `/var/data/uploads` | Persistent disk mount path for uploaded PDFs |
| `VITE_API_URL` (Frontend only) | **Yes** | `https://your-backend.onrender.com/api/v1` | Base API URL consumed by React frontend client |

---

## 4. Persistent Storage vs. Ephemeral Free Tier

> [!WARNING]
> Render Free Tier instances use an **ephemeral container filesystem**. If deployed on the Free tier without a persistent disk:
> 1. Any restarts will reset ChromaDB vector embeddings and uploaded PDFs.
> 2. The database will reset if using SQLite.

### Recommended Production Storage Architecture:
1. **Render Persistent Disk**:
   - In Render Dashboard -> Backend Service -> **Disks** -> **Add Disk**:
     - **Name**: `chatbot-data`
     - **Mount Path**: `/var/data`
     - **Size**: 1 GB or 5 GB
   - Set environment variables:
     - `CHROMA_PERSIST_DIR=/var/data/chroma_data`
     - `UPLOAD_DIR=/var/data/uploads`
     - `POSTGRES_URL=sqlite:////var/data/chatbot.db` (or attach Render Managed PostgreSQL).
2. **Initial Corpus Seeding on New Disk**:
   - Run the initial seed command once via Render Shell or SSH:
     ```bash
     python backend/seed_documents/seed_odisha_schemes.py
     ```

---

## 5. Pre-Deployment Verification Checklist

- [ ] Dedicated audit branch (`audit/production-readiness`) merged to `main` with all fixes.
- [ ] No `.env` or credential files staged or committed to Git (`git status`).
- [ ] `data/raw_pdfs/` excluded from git tracking.
- [ ] Full backend test suite passes: `pytest` (102 tests passing).
- [ ] Frontend build verified: `cd frontend && npm run build` (Exit code 0).
- [ ] Bandit security scan clean: `bandit -r backend -ll -ii` (0 Medium/High issues).
- [ ] Strong `SECRET_KEY` generated with `openssl rand -hex 32`.
- [ ] `render.yaml` present in repository root for infrastructure-as-code deployment.

---

## 6. Post-Deployment Smoke Tests

Execute these verification commands against your live Render backend URL:

```bash
# 1. Health Probe
curl -f https://your-backend.onrender.com/healthz
# Expected: {"status":"ok","version":"2.0.0","environment":"production"}

# 2. Dependency Readiness Probe
curl -f https://your-backend.onrender.com/readyz
# Expected: {"status":"ready","database":"ok","vector_store":"ok (...)","bm25_index":"ok (...)"}

# 3. Prometheus Metrics Endpoint
curl -f https://your-backend.onrender.com/metrics | grep http_requests_total

# 4. Student Registration
curl -X POST https://your-backend.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test_student@domain.com","password":"StrongPassword123!"}'

# 5. User Login
curl -X POST https://your-backend.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test_student@domain.com","password":"StrongPassword123!"}'

# 6. Chat Query with JWT Token
curl -X POST https://your-backend.onrender.com/api/v1/chat \
  -H "Authorization: Bearer <TOKEN_FROM_STEP_5>" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the financial support under KALIA Yojana?"}'
```

---

## 7. Rollback & Disaster Recovery Procedures

1. **Instant Rollback**:
   - In Render Dashboard -> **Deploys** tab -> Select previous successful deploy -> Click **Rollback to this deploy**.
2. **Database Schema Rollback**:
   - If a migration caused degradation:
     ```bash
     alembic downgrade -1
     ```
3. **Corpus Recovery**:
   - If ChromaDB index becomes corrupted, delete contents of `chroma_data/` and run:
     ```bash
     python backend/seed_documents/seed_odisha_schemes.py
     ```
   - BM25 and ChromaDB will re-index all seed schemes within 5 seconds.
