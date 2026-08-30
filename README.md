<div align="center">

# 🌐 Language Agnostic Chatbot

### Multi-Layer Semantic Knowledge Orchestration for Cross-Lingual Conversational AI

*SIH25104 — Smart India Hackathon 2025*

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://langchain.com)
[![Gemini](https://img.shields.io/badge/Gemini-AI-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-FF6B35?style=flat-square)](https://trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<br/>

> **Ask in any language. Get answers grounded in verified government documents.**
> English · हिंदी · Hinglish · ଓଡ଼ିଆ — zero hallucinations, full source citations.

</div>

---

## ✨ What It Does

This system allows citizens to query government welfare schemes, scholarships, pension policies, and agricultural programs in **their native language** — and receive precise, citation-backed answers drawn exclusively from official documents.

| Capability | Detail |
|---|---|
| 🌍 **Multilingual** | English, Hindi, Hinglish, Odia — auto-detected per query |
| 🔍 **Hybrid Retrieval** | Vector (ChromaDB) + BM25 + Reciprocal Rank Fusion + Reranker |
| 🛡️ **Zero-Hallucination** | 100% out-of-domain fallback rate — never makes up answers |
| 📄 **Source Citations** | Every response links back to the source document & section |
| 🏛️ **Admin Dashboard** | Upload PDFs, approve documents, monitor unanswered queries |
| 🔒 **JWT Auth** | Role-based access (Student / Admin) with secure token auth |
| ⚡ **1.18 ms Pipeline** | End-to-end retrieval + generation latency |

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshots/02_login.png" alt="Login Page" width="100%"/>
      <br/><sub><b>🔐 Sign In Page</b> — Clean JWT-secured login for students and admins</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshots/01_chat_homepage.png" alt="Chat Interface" width="100%"/>
      <br/><sub><b>💬 Chat Interface</b> — Query starter cards across all 4 supported languages</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshots/05_chat_response_multilingual.png" alt="Multilingual Response" width="100%"/>
      <br/><sub><b>🌍 Multilingual Response</b> — Auto-detect dropdown with grounded citation-backed answers</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshots/03_admin_documents.png" alt="Admin Documents" width="100%"/>
      <br/><sub><b>🏛️ Admin — Document Manager</b> — Versioned scheme PDFs with status, checksum & actions</sub>
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      <img src="docs/screenshots/04_admin_upload.png" alt="Admin Upload" width="60%"/>
      <br/><sub><b>📤 Admin — Upload & Ingest</b> — Drag-and-drop PDF ingestion with metadata tagging</sub>
    </td>
  </tr>
</table>

---

## 🏗️ Architecture

```
                     ┌─────────────────────────────┐
                     │        React Frontend        │
                     │  Login · Chat · Admin Panel  │
                     └──────────────┬──────────────┘
                                    │ REST API (JWT)
                     ┌──────────────▼──────────────┐
                     │       FastAPI Backend        │
                     │                             │
                     │  ┌──────────────────────┐   │
      Query ────────►│  │   Language Detector  │   │
                     │  │  en · hi · hi-en · or│   │
                     │  └─────────┬────────────┘   │
                     │            │                 │
                     │  ┌─────────▼────────────┐   │
                     │  │   Query Processor    │   │
                     │  │   Rewrite + Expand   │   │
                     │  └─────────┬────────────┘   │
                     │            │                 │
                     │  ┌─────────▼────────────┐   │
                     │  │   Hybrid Retriever   │   │
                     │  │  Vector + BM25 + RRF │   │
                     │  └─────────┬────────────┘   │
                     │            │                 │
                     │  ┌─────────▼────────────┐   │
                     │  │      Reranker        │   │
                     │  │  Semantic Reranking  │   │
                     │  └─────────┬────────────┘   │
                     │            │                 │
                     │  ┌─────────▼────────────┐   │
                     │  │  Evidence Validator  │   │
                     │  │  Grounding + Sources │   │
                     │  └─────────┬────────────┘   │
                     │            │                 │
                     │  ┌─────────▼────────────┐   │
                     │  │     Gemini LLM       │   │
                     │  │  Generate Response   │   │
                     │  └──────────────────────┘   │
                     └─────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
       ┌──────▼──────┐     ┌────────▼───────┐     ┌──────▼──────┐
       │  ChromaDB   │     │   SQLite DB    │     │  BM25 Index │
       │  Embeddings │     │  Users · Docs  │     │  Sparse Ret.│
       └─────────────┘     └────────────────┘     └─────────────┘
```

---

## 📊 Benchmark Results

> Evaluated on 100 structured records across 4 languages with adversarial test cases.

### Retrieval Strategy Comparison

| Strategy | Recall@5 | MRR | Latency |
|---|:---:|:---:|:---:|
| Vector Only | 0.852 | 0.742 | 0.23 ms |
| BM25 Only | 0.938 | 0.842 | 0.18 ms |
| Vector + BM25 + RRF | 0.975 | 0.889 | 0.44 ms |
| **Vector + BM25 + RRF + Reranker** ✅ | **0.988** | **0.913** | **0.59 ms** |

### Language Coverage

| Language | Recall@5 | MRR | Detection Accuracy |
|---|:---:|:---:|:---:|
| English | 1.000 | 0.952 | 92% |
| Hindi | 1.000 | 0.933 | 100% |
| Hinglish | 0.950 | 0.888 | 84% |
| Odia | 1.000 | 0.875 | 100% |
| **Overall** | **0.988** | **0.913** | **94%** |

### Key Metrics

```
🎯  Hallucination Defense Rate  ──────────────────────────── 100.0%  (19/19)
📚  Citation Integrity          ──────────────────────────── 100.0%
🔗  Cross-Language Doc Overlap  ──────────────────────────── 100.0%  IoU
⚡  End-to-End Pipeline Latency ───────────────────────────    1.18 ms
✅  Automated Test Suite        ────────────────────────────  10/10 passed
```

---

## 🗂️ Project Structure

```
language-agnostic-chatbot/
├── 📄 README.md
├── 🐳 docker-compose.yml
├── 🔒 .gitignore
│
├── backend/                         # FastAPI application
│   ├── main.py                      # App entrypoint & startup
│   ├── config.py                    # Settings & env vars
│   ├── requirements.txt
│   ├── .env.example                 # Copy → .env and fill keys
│   ├── Dockerfile
│   │
│   ├── auth/                        # JWT auth (login, tokens)
│   ├── contracts/                   # Pydantic API schemas
│   ├── ingestion/                   # PDF ingestion pipeline
│   ├── language/                    # Language detection & normalization
│   ├── models/                      # SQLAlchemy DB models & seeding
│   ├── rag/                         # Core RAG engine
│   │   ├── engine.py                # Orchestrates the full pipeline
│   │   ├── vector_store.py          # ChromaDB interface
│   │   ├── bm25.py                  # Sparse retrieval (Okapi BM25)
│   │   ├── fusion.py                # Reciprocal Rank Fusion
│   │   ├── reranker.py              # Semantic reranking
│   │   ├── validator.py             # Evidence grounding & validation
│   │   ├── chain.py                 # LangChain integration
│   │   ├── llm_provider.py          # Gemini LLM wrapper
│   │   ├── prompts.py               # Prompt templates
│   │   └── query_processor.py       # Query rewriting & expansion
│   ├── retrieval/                   # Hybrid retriever orchestrator
│   ├── routers/                     # API route handlers
│   │   ├── chat.py                  # /chat endpoint
│   │   └── admin.py                 # /admin endpoints
│   └── seed_documents/              # Official government scheme PDFs
│
├── frontend/                        # React + Vite application
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── nginx.conf                   # Production serving config
│   ├── Dockerfile
│   └── src/
│       ├── App.jsx                  # Root app + auth context
│       ├── main.jsx
│       ├── api/client.js            # Axios API client
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── ChatPage.jsx
│       │   └── AdminPage.jsx
│       └── styles/globals.css
│
├── tests/                           # Automated test suite
│   ├── test_rag_pipeline.py
│   ├── test_master_engineering_suite.py
│   └── test_provenance_and_versioning.py
│
└── evaluation/                      # Benchmarking & evaluation
    ├── dataset.json                 # 100-record multilingual dataset
    ├── metrics.json
    ├── results.json
    ├── report.md                    # Full benchmark report
    ├── generate_dataset.py
    └── run_benchmarks.py
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### Option A — Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/your-username/language-agnostic-chatbot.git
cd language-agnostic-chatbot

# Set your API key
cp backend/.env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY

# Launch everything
docker-compose up --build
```

| Service | URL |
|---|---|
| 🖥️ Frontend | http://localhost:5173 |
| ⚙️ Backend API | http://localhost:8000 |
| 📚 Swagger Docs | http://localhost:8000/docs |

---

### Option B — Local Development

**1. Backend**

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set GEMINI_API_KEY at minimum

# Start the API server
uvicorn backend.main:app --reload --port 8000
```

**2. Frontend**

```bash
cd frontend

npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🔐 Demo Accounts

| Role | Email | Password |
|---|---|---|
| 👨‍🎓 Student | `student@demo.com` | `demo123` |
| 🛡️ Admin | `admin@demo.com` | `admin123` |

---

## ⚙️ Environment Variables

Copy `backend/.env.example` → `backend/.env` and configure:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Database
POSTGRES_URL=sqlite:///./chatbot.db

# Auth
SECRET_KEY=change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Vector Store
CHROMA_PERSIST_DIR=./chroma_data
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# RAG Settings
GEMINI_MODEL=gemini-2.0-flash
RETRIEVAL_K=5
CONFIDENCE_THRESHOLD=0.25
```

---

## 🧪 Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the full test suite
pytest tests/ -v

# Run evaluation benchmarks
python evaluation/run_benchmarks.py
```

---

## 🌍 Supported Languages

| Language | Code | Script | Example Query |
|---|---|---|---|
| English | `en` | Latin | *"What is the KALIA scheme benefit?"* |
| Hindi | `hi` | Devanagari | *"कालिया योजना के तहत सहायता क्या है?"* |
| Hinglish | `hi-en` | Mixed | *"KALIA scheme mein kitna paisa milta hai?"* |
| Odia | `or` | Odia | *"କାଲିଆ ଯୋଜନାରେ ସୁବିଧା କ'ଣ?"* |

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini 2.0 Flash |
| **Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` |
| **Vector Store** | ChromaDB |
| **Sparse Retrieval** | Okapi BM25 |
| **Fusion** | Reciprocal Rank Fusion (RRF) |
| **Backend** | FastAPI · SQLAlchemy · SQLite |
| **Frontend** | React 18 · Vite |
| **Auth** | JWT (python-jose · passlib) |
| **PDF Parsing** | PyMuPDF |
| **Orchestration** | LangChain |
| **Containerization** | Docker · Docker Compose |

---

## 📋 API Reference

Full interactive docs at **http://localhost:8000/docs** (Swagger UI).

| Endpoint | Method | Description |
|---|---|---|
| `/auth/login` | `POST` | Authenticate and receive JWT token |
| `/chat/query` | `POST` | Submit a multilingual query |
| `/admin/documents` | `GET` | List all managed documents |
| `/admin/documents` | `POST` | Upload and ingest a new PDF |
| `/admin/documents/{id}` | `PATCH` | Approve or archive a document |
| `/admin/documents/{id}` | `DELETE` | Remove a document |
| `/admin/unanswered-queries` | `GET` | Queries that triggered fallback |
| `/admin/analytics` | `GET` | Usage statistics |
| `/health` | `GET` | Service health check |

---

## 🗺️ Roadmap

- [ ] Odia morphological stemmer integration
- [ ] Pre-packaged offline embedding weights in Docker image
- [ ] Dual-retrieval for multi-intent cross-scheme queries
- [ ] Table-aware PDF extraction for nested gazette tables
- [ ] Timestamp-weighted contradiction auto-resolution
- [ ] PostgreSQL production backend
- [ ] Streaming chat responses (Server-Sent Events)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Made with ❤️ for making government information accessible to every citizen

*Built for Smart India Hackathon 2025 — Problem Statement SIH25104*

</div>
