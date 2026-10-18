<div align="center">

# 🌐 Language Agnostic Chatbot

### Multi-Layer Semantic Knowledge Orchestration for Cross-Lingual Conversational AI

*SIH25104 — Smart India Hackathon 2025*

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Tests](https://img.shields.io/badge/Tests-102%20Passed-brightgreen?style=flat-square)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-76%25-green?style=flat-square)](docs/audit/TEST_REPORT.md)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Render](https://img.shields.io/badge/Deploy-Render%20Ready-46E3B7?style=flat-square&logo=render&logoColor=white)](render.yaml)

<br/>

> **Ask in any language. Get answers grounded in verified government documents.**  
> English · हिंदी · Hinglish · ଓଡ଼ିଆ — zero hallucinations, full source citations.

</div>

---

## 📑 Production Audit & Verification Deliverables

Complete production-readiness audit reports generated for GitHub publication and Render deployment:

- 📊 **[Repository Audit Report](docs/audit/REPOSITORY_AUDIT.md)**: Inventory of all modules, cleanup actions, tracked seed data, and disposable artifact exclusions.
- 🛡️ **[Security Audit Report](docs/audit/SECURITY_AUDIT.md)**: Static analysis (Bandit), CVE dependency scan (pip-audit), dual-view prompt injection defense, and RBAC matrix.
- 🔌 **[API Audit & Endpoint Inventory](docs/audit/API_AUDIT.md)**: Complete 27-endpoint inventory, request schemas, SSE streaming contracts, and error structures.
- 📈 **[RAG & Multilingual Evaluation Report](docs/audit/RAG_EVALUATION.md)**: 100-sample empirical benchmark results (Recall@k, MRR, ablation, citation accuracy, hallucination rates).
- ⚡ **[Performance & Concurrency Benchmark](docs/audit/PERFORMANCE_BENCHMARK.md)**: Cold-start vs. warm latencies (P50/P95), throughput up to 25 concurrent users, memory footprint.
- 🧪 **[Test & Coverage Report](docs/audit/TEST_REPORT.md)**: 102 passed unit/integration tests, 76% statement coverage, and regression verifications.
- 🚀 **[Render Deployment Checklist](docs/audit/DEPLOYMENT_CHECKLIST.md)**: Turnkey Render Web Service and Static Site configurations, disk persistence, and rollback instructions.

---

## ✨ Project Purpose & Capabilities

Language Agnostic Chatbot enables citizens to query complex government welfare schemes, scholarships, pension guidelines, and agricultural policies in their **native language or mixed scripts (Hinglish)**. The system retrieves verified institutional documents and synthesizes fact-checked answers with strict source citations, preventing LLM hallucinations.

| Capability | Detail |
|---|---|
| 🌍 **Multilingual** | English, Hindi, Hinglish, and Odia with automated language identification |
| 🔍 **Hybrid Retrieval** | Dense semantic vector search (ChromaDB) + Sparse lexical (Okapi BM25) + RRF + Reranker |
| 🛡️ **Anti-Hallucination Gate** | 100% out-of-domain fallback rate — abstains when retrieved evidence is insufficient |
| 📄 **Source Citations** | Every response links back to the verified document, page, and section |
| ⚡ **Real-Time Streaming** | Low-latency response streaming via Server-Sent Events (SSE) |
| 🏛️ **Admin Management** | Drag-and-drop PDF ingestion, SHA-256 deduplication, status approval, and unanswered query triage |
| 🏢 **Multi-Tenant SaaS** | Organization-level isolation for documents, vector collections, and user conversations |
| 🛡️ **Hardened Security** | Dual-view Unicode prompt injection filter, OWASP-compliant upload guards, and JWT RBAC |

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshots/02_login.png" alt="Login Page" width="100%"/>
      <br/><sub><b>🔐 Sign In Page</b> — Secure JWT-authenticated login for citizens and administrators</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshots/01_chat_homepage.png" alt="Chat Interface" width="100%"/>
      <br/><sub><b>💬 Chat Interface</b> — Multilingual query starters and conversational history</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshots/05_chat_response_multilingual.png" alt="Multilingual Response" width="100%"/>
      <br/><sub><b>🌍 Multilingual Response</b> — Language detection with grounded citations</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshots/03_admin_documents.png" alt="Admin Documents" width="100%"/>
      <br/><sub><b>🏛️ Admin Document Manager</b> — Versioned scheme PDFs with checksums and approval status</sub>
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      <img src="docs/screenshots/04_admin_upload.png" alt="Admin Upload" width="60%"/>
      <br/><sub><b>📤 Admin PDF Ingestion</b> — Binary magic byte validation, PyMuPDF integrity check</sub>
    </td>
  </tr>
</table>

---

## 🏗️ Architecture & Request Flow

```
Citizens / Admins (Web / Mobile)
               │
               ▼
   ┌───────────────────────┐
   │ React 18 + Vite SPA   │
   └───────────┬───────────┘
               │ HTTPS (Bearer JWT / SSE)
               ▼
   ┌───────────────────────────────────────────────────────────┐
   │ FastAPI Application Gateway                               │
   │  - Request ID & Prometheus Metrics Middleware             │
   │  - Dual-View Unicode Prompt Injection Defense             │
   │  - RBAC Security Gate (Student / Admin / Super Admin)     │
   └───────────┬───────────────────────────────────────────────┘
               │
               ▼
   ┌───────────────────────────────────────────────────────────┐
   │ Modular RAG Orchestration Engine                          │
   │  1. Language Normalization & Intent Detection             │
   │  2. Dual-Engine Hybrid Retrieval                          │
   │     ├── ChromaDB Dense Embeddings (MiniLM-L12-v2)         │
   │     └── Okapi BM25 Sparse Lexical Inverted Index          │
   │  3. Reciprocal Rank Fusion (RRF k=60) & Reranker          │
   │  4. Evidence Grounding & Contradiction Validator          │
   │  5. LLM Synthesis (Groq Llama 3.3 / Gemini Flash Fallback)│
   └───────────┬───────────────────────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│ PostgreSQL / │ │ ChromaDB     │
│ SQLite DB    │ │ Vector Store │
└──────────────┘ └──────────────┘
```

---

## 🔧 Verified Technology Stack

- **Backend**: Python 3.9+ / 3.11, FastAPI 0.128, Uvicorn, Starlette
- **Primary LLM Provider**: Groq API (`llama-3.3-70b-versatile` / `qwen/qwen3.8-27b`)
- **Fallback LLM Provider**: Google Gemini API (`gemini-3.1-flash-lite`)
- **Vector Embeddings**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions)
- **Vector Database**: ChromaDB 1.5+ (Persistent HNSW + SQLite metadata)
- **Lexical Search**: Okapi BM25 Index with multilingual tokenization
- **Relational Storage**: PostgreSQL 15+ (Production) / SQLite 3 (Development) via SQLAlchemy 2.0 & Alembic
- **Document Processing**: PyMuPDF (`fitz`), Pillow, Tesseract OCR (`tesseract-ocr-eng`, `tesseract-ocr-hin`, `tesseract-ocr-ori`)
- **Security & Auth**: `python-jose`, `passlib[bcrypt]`, PBKDF2-SHA256, Unicode NFKC sanitization
- **Frontend**: React 18, Vite 5, React Router 6, Axios, Modern Vanilla CSS Design Tokens
- **Observability**: Prometheus metrics exposition (`/metrics`), JSON structured logging, `/readyz` probes
- **Deployment**: Docker multi-stage builds, Docker Compose, Render Blueprint (`render.yaml`)

---

## 📊 Measured Evaluation Results

Empirically measured using `evaluation/run_full_empirical_evaluation.py` on the 100-sample benchmark dataset (`evaluation/dataset.json`):

| Evaluation Dimension | Metric | Measured Value | Notes |
|---|---|---|---|
| **Retrieval Accuracy** | Recall@1 | **72.84%** | First result contains target document |
| | Recall@5 | **76.54%** | Top-5 candidates contain target document |
| | MRR (Mean Reciprocal Rank) | **0.7469** | Rank quality across all queries |
| **Language Retrieval** | English (`en`) Recall@5 | **95.24%** | High semantic-lexical convergence |
| | Hinglish (`hi-en`) Recall@5 | **75.00%** | Mixed Latin-Hindi script normalized |
| | Hindi (`hi`) Recall@5 | **60.00%** | Devanagari script retrieval |
| | Odia (`or`) Recall@5 | **0.00%** | *Documented Limitation*: Seed corpus is in English/Hindi |
| **Groundedness & Safety** | Grounded Answer Rate | **100.0%** | Answers drawn exclusively from context |
| | Citation Coverage | **100.0%** | Every answer includes source metadata |
| | Citation Correctness | **76.54%** | Exact ground-truth document cited |
| | Prompt Injection Defense | **100.0%** (17/17) | 0 false positives on valid citizen queries |
| **System Latency** | Warm Retrieval P50 | **32.76 ms** | In-memory embedding & BM25 lookup |
| | Warm Retrieval P95 | **38.04 ms** | 95th percentile under continuous traffic |
| | Concurrency Throughput | **35.9 req/s** | Tested up to 25 simultaneous users |
| | Peak RAM Footprint | **886.7 MB** | Includes PyTorch weights and ChromaDB |

---

## ⚙️ Environment Variables

Create `backend/.env` based on `backend/.env.example`:

| Variable | Required | Default / Example | Purpose |
|---|---|---|---|
| `GROQ_API_KEY` | **Yes** (Primary) | `gsk_your_groq_key_here` | Groq API Key (Free tier at https://console.groq.com/keys) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model identifier |
| `LLM_PROVIDER` | No | `groq` | Provider selector (`groq`, `gemini`, or `mock`) |
| `GEMINI_API_KEY` | Optional | `your_gemini_api_key_here` | Fallback LLM API Key (https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL` | No | `gemini-3.1-flash-lite` | Gemini model identifier |
| `ENVIRONMENT` | **Yes** | `development` / `production` | Production mode enables strict security guards |
| `SECRET_KEY` | **Yes** | `min-32-chars-random-string` | JWT encryption secret key (generate with `openssl rand -hex 32`) |
| `ALGORITHM` | No | `HS256` | JWT signature algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | JWT expiration duration (24 hours) |
| `POSTGRES_URL` | No | `sqlite:///./chatbot.db` | Database URL (set PostgreSQL URL for production) |
| `CORS_ORIGINS` | **Yes** | `http://localhost:5173,http://localhost:3000` | Comma-separated list of allowed frontend origins |
| `CHROMA_PERSIST_DIR` | No | `./chroma_data` | Persistent disk storage location for vector DB |
| `EMBEDDING_MODEL` | No | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | SentenceTransformer model |
| `MAX_UPLOAD_SIZE_MB` | No | `25` | Maximum PDF file upload size limit |

---

## 🚀 Local Installation & Setup

### Prerequisites
- Python 3.9+ (Python 3.11 recommended)
- Node.js 18+ and npm
- Tesseract OCR (Optional, required only for scanned PDF OCR):
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-hin tesseract-ocr-ori`

### Option 1 — Quickstart with Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-username/language-agnostic-chatbot.git
cd language-agnostic-chatbot

# Create backend environment file
cp backend/.env.example backend/.env
# Set GROQ_API_KEY in backend/.env

# Build and start all services (Backend, Frontend, PostgreSQL)
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Documentation**: http://localhost:8000/docs

---

### Option 2 — Local Development (Manual)

#### 1. Backend Setup
```bash
# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp backend/.env.example backend/.env
# Add your GROQ_API_KEY in backend/.env

# Seed initial Odisha welfare scheme documents into ChromaDB & SQLite
python backend/seed_documents/seed_odisha_schemes.py

# Start FastAPI server with live reloading
uvicorn backend.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 📚 Seed Documents & Incremental Ingestion CLI

The repository includes seed documents for major Odisha government welfare programs:
1. **KALIA Yojana** (Krushak Assistance for Livelihood and Income Augmentation)
2. **Biju Swasthya Kalyan Yojana (BSKY)** (Universal Health Coverage)
3. **Madhu Babu Pension Yojana (MBPY)** (Social Security & Disability Pension)
4. **Odisha State Post-Matric & Merit Scholarship** (Higher Education Support)

### Incremental Portal Ingestion CLI (`ingest.py`)
To ingest documents directly from departmental portals:
```bash
# Ingest Priority 1 (Agriculture & Farmers' Empowerment)
python ingest.py "PROCESS PRIORITY 1"

# Ingest Priority 2 (Social Security & Empowerment)
python ingest.py "PROCESS PRIORITY 2"

# Ingest specific department by name
python ingest.py "PROCESS AGRICULTURE"
```

---

## 📋 API Endpoints Reference

Interactive OpenAPI documentation is live at `/docs` (Swagger UI) and `/redoc`.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new student user | Public |
| `POST` | `/api/v1/auth/login` | Authenticate user and receive JWT Bearer token | Public |
| `POST` | `/api/v1/chat` | Send conversational query (synchronous response) | Bearer JWT |
| `POST` | `/api/v1/chat/stream` | Send conversational query with real-time SSE streaming | Bearer JWT |
| `GET` | `/api/v1/conversations` | List citizen's conversation history | Bearer JWT |
| `POST` | `/api/v1/admin/documents` | Upload and ingest official scheme PDF | Admin JWT |
| `GET` | `/api/v1/admin/documents` | List uploaded documents with status and checksums | Admin JWT |
| `PATCH` | `/api/v1/admin/documents/{id}` | Approve, reject, or archive document | Admin JWT |
| `GET` | `/healthz` | Lightweight process liveness probe | Public |
| `GET` | `/readyz` | Deep readiness probe (Database, Vector Store, BM25) | Public |
| `GET` | `/metrics` | Prometheus exposition format metrics | Public |

### Example Chat Request:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the financial assistance provided under KALIA Yojana?",
    "preferred_language": "en"
  }'
```

---

## 🧪 Testing & Verification Commands

```bash
# Activate virtual environment
source venv/bin/activate

# 1. Run all 102 backend unit and integration tests
pytest

# 2. Run with code coverage reporting
pytest --cov=backend --cov-report=term-missing

# 3. Run security regression suite specifically
pytest tests/test_security_suite.py -v

# 4. Run static security analysis (Bandit)
bandit -r backend -ll -ii

# 5. Run full empirical RAG benchmark (100 ground-truth queries)
python evaluation/run_full_empirical_evaluation.py

# 6. Verify frontend production build
cd frontend && npm run build
```

---

## ☁️ Render Deployment Guide

The repository includes a turnkey `render.yaml` Blueprint for one-click deployment.

### Deploying via Render Blueprint:
1. Push your repository to GitHub.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub repository. Render reads `render.yaml` and provisions:
   - **`language-agnostic-chatbot-backend`** (Web Service on Python runtime)
   - **`language-agnostic-chatbot-frontend`** (Static Site on Node runtime)
5. Fill in your secret environment variables in the Render Dashboard:
   - `GROQ_API_KEY`: Your Groq API key
   - `SECRET_KEY`: A 32-character random string (`openssl rand -hex 32`)
   - `CORS_ORIGINS`: Your Render frontend URL (e.g. `https://language-agnostic-chatbot-frontend.onrender.com`)

### Persistent Storage Note:
For production ChromaDB and PDF persistence on Render, attach a **Persistent Disk** mounted at `/var/data` and configure `CHROMA_PERSIST_DIR=/var/data/chroma_data` and `UPLOAD_DIR=/var/data/uploads`. See [Deployment Checklist](docs/audit/DEPLOYMENT_CHECKLIST.md) for full instructions.

---

## 🛡️ Security Considerations & Limitations

- **Production Seed Guard**: Demo users (`student@demo.com` and `admin@demo.com`) are automatically blocked from creation when `ENVIRONMENT=production`. In production, administrators must be provisioned securely.
- **Prompt Injection Defense**: Dual-view Unicode NFKC sanitization strips invisible characters and detects role overrides, jailbreaks, and prompt boundary tokens on both unary and streaming endpoints.
- **Odia Language Retrieval Limitation**: In the current version, native Odia script queries achieve 0.0% recall on English policy documents because the seed documents are drafted in English with Hindi summaries. The evidence validation layer successfully catches these cases and returns a clean, safe fallback instead of hallucinating. Ingesting native Odia government publications via `ingest.py` resolves this constraint.

---

## 📄 License & Contributing

- **License**: Licensed under the [MIT License](LICENSE).
- **Security Inquiries**: Please review our [Security Policy](SECURITY.md) for vulnerability disclosure.
- **Contributing**: Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

<br/>

<div align="center">
Made with ❤️ for making government scheme access transparent, equitable, and multilingual for every citizen.
</div>
