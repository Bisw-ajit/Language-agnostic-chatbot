# Product Requirements Document (PRD)
## SIH25104 — Language Agnostic Chatbot
### A Multi Layer Semantic Knowledge Orchestration Framework for Cross Lingual Conversational Information Processing

**Version:** 1.0
**Prepared for:** Building this project with **Google Antigravity** (agent-first IDE)
**Companion doc:** `01_Team_Split_and_Roadmap.md`

> **How to use this PRD with Antigravity:** Antigravity works best when you give an agent a scoped, verifiable goal rather than the whole PRD at once. Section 12 ("Agent Mission Breakdown") turns this PRD into individually dispatchable missions — paste one mission at a time into Antigravity's Agent Manager, in order, and use the Acceptance Criteria as what you check in the Artifacts (task list / walkthrough / screenshots) it produces before merging. Section 13 gives suggested Antigravity **Rules** and **Workflows** (saved markdown files Antigravity can reuse) so every agent run follows the same conventions.

---

## 1. Overview

### 1.1 Problem statement
Students and citizens need to access institutional information (scholarships, admissions, hostel rules, exam regulations, fees) but official documents are long, siloed, and language-specific. Users ask the same question in different languages or mixed-language form (English, Hindi, Hinglish, and other Indian regional languages). There is no reliable way to ask a question in one's own language and get a grounded, sourced answer.

### 1.2 Solution
A multilingual, context-aware, Retrieval-Augmented Generation (RAG) chatbot that:
- Understands a query regardless of language/code-mixing
- Retrieves relevant chunks from a controlled, admin-curated knowledge base
- Maintains conversational context across turns
- Generates a grounded answer, in the user's language, with a visible source and page reference
- Refuses to answer (rather than fabricate) when confidence is low

### 1.3 Non-goals (explicitly out of scope for v1)
- Supporting every Indian language — start with a validated core set (English, Hindi, Hinglish, +1 regional language such as Odia) and expand only after evaluation
- Voice or video interaction
- Integration with external messaging platforms (WhatsApp, Telegram, SMS)
- Fine-tuning or training a language model from scratch
- Complex multi-agent (CrewAI) orchestration — only add if the single-pipeline RAG proves insufficient
- Mobile native apps

---

## 2. Users & Personas

| Persona | Needs |
|---|---|
| **Student/Citizen (primary user)** | Ask a question in their own language, get a fast, trustworthy, sourced answer; ask follow-ups naturally |
| **Institution Admin** | Upload/update/remove official documents; approve documents before they become searchable; see what questions are going unanswered |
| **Super Admin** | Manage admins, view system-wide analytics, manage supported languages |

---

## 3. Functional Requirements

Numbered, testable requirements. Each has an ID (`FR-xx`) referenced later in acceptance criteria.

### Language & Query Understanding
- **FR-01:** System shall detect the language of an incoming message (from the validated language set).
- **FR-02:** System shall detect code-mixed (e.g., Hinglish) input and normalize it for downstream processing.
- **FR-03:** System shall preserve the user's original message unmodified in storage; normalization happens on a working copy.

### Knowledge Retrieval
- **FR-04:** System shall retrieve the top-K most semantically relevant document chunks for a normalized query, using multilingual embeddings, regardless of the language the source document was written in (cross-lingual retrieval).
- **FR-05:** System shall support metadata filtering (e.g., by department, document version, language) during retrieval.
- **FR-06:** System shall support re-indexing when a document is updated, without requiring a full system restart.

### Answer Generation
- **FR-07:** System shall generate answers strictly grounded in retrieved context; the system prompt shall explicitly forbid answering from unsupported model knowledge.
- **FR-08:** System shall respond in the user's detected/preferred language, independent of the language of the source document.
- **FR-09:** System shall attach source document name + page/section to every grounded answer.
- **FR-10:** When retrieval confidence is below a configurable threshold, system shall return a fallback message instead of a generated answer (see FR-16 for the exact message pattern).

### Conversation Context
- **FR-11:** System shall maintain conversation history per `conversation_id`.
- **FR-12:** System shall rewrite follow-up queries using conversation history before retrieval (e.g., "what documents do I need?" → resolved against the prior topic).
- **FR-13:** The rewritten/expanded query shall not be shown to the user; only the natural response is shown.

### Trust & Safety
- **FR-14:** System shall never fabricate institutional facts (deadlines, amounts, eligibility) not present in retrieved context.
- **FR-15:** System shall log every query, retrieval result set, and final answer for admin review (with PII handled per Section 8).
- **FR-16:** Fallback message shall be a clear, non-technical statement, e.g., *"I couldn't find reliable information about that in the available institutional knowledge base."* — never a silent wrong answer.

### Admin & Content Management
- **FR-17:** Admin shall be able to upload a document (PDF at minimum for v1).
- **FR-18:** Uploaded documents shall enter a `pending → validated → approved → indexed` workflow; only `indexed` documents are searchable by the chatbot.
- **FR-19:** Admin shall be able to delete or supersede (version) a document; superseded versions shall stop being retrieved.
- **FR-20:** Admin shall be able to view: indexing status, unanswered/fallback queries, and user feedback.
- **FR-21:** Super Admin shall be able to manage admin accounts and the list of supported languages.

### Feedback & Analytics
- **FR-22:** User shall be able to give thumbs up/down feedback on any answer.
- **FR-23:** System shall expose aggregate analytics: total queries, successful-retrieval rate, fallback rate, average/P95 latency, most-used language, top topics.

---

## 4. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Latency** | P95 end-to-end response time ≤ 3.5s for a grounded answer in MVP; target ≤ 2s post-optimization |
| **Groundedness** | ≥ 95% of answers on the labeled eval set must be traceable to a cited chunk (no unsupported claims) |
| **Fallback correctness** | ≥ 90% of out-of-scope/adversarial test questions must trigger fallback, not a fabricated answer |
| **Multilingual parity** | Retrieval accuracy (Recall@5) for Hindi and Hinglish queries must be within 15% relative of English on the same eval set, or the gap must be explicitly documented |
| **Availability** | Single-node deployment should recover automatically (Docker restart policy) from a crashed container |
| **Security** | All admin routes require authenticated, role-checked access; student role cannot write to knowledge base |
| **Scalability (design-only for v1)** | Architecture must not preclude adding languages or document domains without a rebuild (modular embedding/retrieval layer) |
| **Observability** | Every request traceable via a request/trace ID through gateway → retrieval → LLM → response |

---

## 5. System Architecture (target reference)

```
USER
 │
 ▼
React.js Frontend  ───────────────────────────────────────────┐
 │  (chat UI, admin UI)                                        │
 ▼                                                              │
FastAPI API Gateway (auth, validation, routing)                │
 │                                                               │
 ▼                                                               │
Language Understanding  →  Semantic Processing (embeddings)     │
 │                              │                                │
 │                              ▼                                │
 │                        ChromaDB (vector search + metadata)    │
 │                              │                                │
 ▼                              ▼                                │
Context/Conversation Mgmt  ←  Top-K Retrieved Chunks             │
 │                                                                │
 ▼                                                                │
LLM Response Engine (LangChain RAG chain, grounded prompting)    │
 │                                                                │
 ▼                                                                │
Response Validation (groundedness, confidence, language check)  │
 │                                                                │
 ▼                                                                │
Response + Source/Citation  ──────────────────────────────────► back to UI

Side systems: PostgreSQL (users, conversations, messages, feedback,
document_metadata, analytics)  |  Docker (all services containerized)
```

---

## 6. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React.js | Chat UI + Admin UI |
| Backend/API | FastAPI (Python) | REST, async, Pydantic validation |
| Orchestration | LangChain | RAG chain, prompt templates |
| Embeddings/NLP | Hugging Face models | Multilingual sentence embeddings + language ID |
| Vector DB | ChromaDB | Chunk storage + semantic search |
| Relational DB | PostgreSQL | Structured app data |
| Containerization | Docker + docker-compose | Local & deployment parity |
| Multi-agent (deferred) | CrewAI | Only if router/retriever/LLM pipeline proves insufficient |

**Principle carried over from project context:** do not add a technology (e.g. CrewAI) to the MVP just because it's on the original form — justify each addition against a real limitation of the simpler pipeline.

---

## 7. Data Models

### 7.1 PostgreSQL schema (minimum viable)

```sql
users (
  id UUID PRIMARY KEY,
  name TEXT,
  role TEXT CHECK (role IN ('student','admin','super_admin')),
  preferred_language TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

conversations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

messages (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  role TEXT CHECK (role IN ('user','assistant')),
  message TEXT,
  language TEXT,
  confidence NUMERIC,
  sources JSONB,
  timestamp TIMESTAMPTZ DEFAULT now()
);

feedback (
  id UUID PRIMARY KEY,
  message_id UUID REFERENCES messages(id),
  rating TEXT CHECK (rating IN ('up','down')),
  comment TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

document_metadata (
  id UUID PRIMARY KEY,
  filename TEXT,
  department TEXT,
  language TEXT,
  version TEXT,
  status TEXT CHECK (status IN ('pending','validated','approved','indexed','superseded')),
  uploaded_by UUID REFERENCES users(id),
  uploaded_at TIMESTAMPTZ DEFAULT now()
);

analytics_daily (
  date DATE PRIMARY KEY,
  total_queries INT,
  successful_retrievals INT,
  fallback_queries INT,
  avg_latency_ms INT,
  top_language TEXT,
  top_topic TEXT
);
```

### 7.2 ChromaDB chunk metadata

```json
{
  "text": "<chunk text>",
  "source": "scholarship_policy.pdf",
  "page": 12,
  "department": "Student Welfare",
  "language": "English",
  "version": "2026",
  "document_id": "<uuid matching document_metadata.id>"
}
```

---

## 8. Security & Privacy

- JWT-based auth; role claim checked on every `/admin/*` route.
- Students cannot call document write endpoints (`POST/PUT/DELETE /admin/documents*`).
- Store the minimum PII necessary (name, preferred language); do not log full message bodies in plaintext monitoring dashboards — keep them in the access-controlled `messages` table only.
- Document ingestion always passes through `pending → validated → approved → indexed`; nothing is searchable straight off an upload.
- Rate limit `/chat` per user/IP to prevent abuse.

---

## 9. API Contract (v1)

```
POST /api/v1/auth/login
POST /api/v1/auth/register

POST /api/v1/chat
  Request:  { "conversation_id": "uuid|null", "message": "string" }
  Response: { "conversation_id": "uuid", "answer": "string",
              "sources": [{"document":"str","page":int}],
              "detected_language": "string", "confidence": float,
              "is_fallback": bool }

POST /api/v1/feedback
  Request: { "message_id": "uuid", "rating": "up|down", "comment": "string|null" }

--- Admin ---
POST   /api/v1/admin/documents            (multipart upload)
GET    /api/v1/admin/documents
PATCH  /api/v1/admin/documents/{id}       (approve / supersede)
DELETE /api/v1/admin/documents/{id}
GET    /api/v1/admin/documents/{id}/status
GET    /api/v1/admin/analytics
GET    /api/v1/admin/unanswered-queries

--- Super Admin ---
POST /api/v1/admin/users                 (create admin)
GET  /api/v1/admin/languages
PUT  /api/v1/admin/languages
```

---

## 10. Evaluation Plan

| Metric | Method | Target (v1) |
|---|---|---|
| Recall@5 / Precision@5 / MRR | Hand-labeled eval set (≥30 Q&A pairs/language) run against retrieval function | Recall@5 ≥ 0.8 English; documented for other languages |
| Faithfulness/Groundedness | Manual review of 50 sampled answers vs. cited source | ≥ 95% pass |
| Fallback correctness | 20 adversarial (unanswerable) questions | ≥ 90% correctly decline |
| Language consistency | 20 queries per supported language | 100% response in requested language |
| Latency | Load test with k6/locust, 20 concurrent users | P95 ≤ 3.5s |

---

## 11. Milestones (maps to roadmap sprints in companion doc)

1. **M1 — Skeleton wired:** React ↔ FastAPI ↔ mock response round-trip works.
2. **M2 — Ungrounded chat works:** Real LLM call, no retrieval yet.
3. **M3 — Grounded RAG works:** Retrieval + citation on ≥5 real documents.
4. **M4 — Multilingual verified:** Same intent in 3 languages retrieves same doc, answers in-language.
5. **M5 — Context works:** 2-turn follow-up resolves correctly.
6. **M6 — Trustworthy:** Fallback triggers correctly on adversarial set; sources always shown.
7. **M7 — Admin loop closed:** Upload → approve → indexed → searchable, via UI only.
8. **M8 — Dockerized & demo-ready:** `docker-compose up` brings the whole system up; demo script passes.

---

## 12. Agent Mission Breakdown (for dispatching to Antigravity)

Each mission below is sized to hand to a single Antigravity agent run. Give the agent the mission text, point it at the relevant contracts (Section 9/7), and use the **Acceptance Criteria** to review its Artifacts (task list, walkthrough, screenshots/test output) before accepting the change. Run missions roughly in order; later missions assume earlier ones are merged.

**Mission A — Repo & contracts scaffold**
> "Set up a monorepo with `/frontend` (React + Vite), `/backend` (FastAPI, Python 3.11), `/contracts` (shared Pydantic + TS types matching Section 9's API contract), and `docker-compose.yml` with placeholder services for backend, frontend, ChromaDB, and PostgreSQL. Add a root README explaining how to run everything locally."
- **Acceptance:** `docker-compose up` boots all 4 services without error; hitting `GET /health` on the backend returns 200.

**Mission B — Auth & role-gated routing**
> "Implement JWT-based auth in FastAPI per Section 8/9: `/auth/register`, `/auth/login`, and role-checked dependency for `student` vs `admin` vs `super_admin`. Reject any `/admin/*` call without the correct role with 403."
- **Acceptance:** Automated tests: student token on an admin route → 403; admin token → 200.

**Mission C — Document ingestion pipeline**
> "Implement the ingestion pipeline described in Section 7.2: PDF text extraction, cleaning, chunking (configurable chunk size/overlap), metadata tagging, embedding via a multilingual Hugging Face model, and upsert into ChromaDB. Expose it as both a CLI script and the `POST /admin/documents` endpoint, gated by the `pending → validated → approved → indexed` status workflow (FR-17/18/19) with the `document_metadata` Postgres table from Section 7.1."
- **Acceptance:** Uploading a sample PDF via the endpoint results in a `document_metadata` row with status transitions, and, after admin approval, chunks appear in ChromaDB with correct metadata.

**Mission D — Retrieval function + eval harness**
> "Implement a `retrieve(query, k, filters)` function performing multilingual semantic search against ChromaDB, returning chunks with scores and metadata (FR-04/05). Build an evaluation script per Section 10 that runs a labeled Q&A set and reports Recall@K, Precision@K, MRR."
- **Acceptance:** Eval script runs end-to-end and prints metrics; Recall@5 on the English subset ≥ 0.8 on the sample set.

**Mission E — Language & code-mix detection**
> "Implement language detection and Hinglish/code-mix detection (FR-01/02/03) as an importable module, integrated into the `/chat` request path before retrieval. Include unit tests covering English, Hindi, Hinglish, and one additional regional language sample set."
- **Acceptance:** Unit tests pass; a mixed 'scholarship ka last date kya hai' sample is correctly flagged as Hinglish.

**Mission F — Grounded RAG chain**
> "Using LangChain, build a RAG chain that takes a normalized query + conversation history, calls Mission D's retrieval, and generates an answer using a system prompt that forbids answering outside the provided context (FR-07/08/09). Attach source document + page to the response. Wire this into `POST /api/v1/chat` per the Section 9 contract."
- **Acceptance:** Asking a question covered by an indexed document returns an answer with a correct source/page; asking something not in any document does not return a fabricated fact.

**Mission G — Confidence & fallback**
> "Add a confidence score to the RAG chain's output and implement the low-confidence fallback behavior from FR-10/FR-16. Build the 20-question adversarial test set described in Section 10 and confirm fallback fires correctly."
- **Acceptance:** ≥ 90% of the adversarial set triggers the fallback message rather than a generated answer.

**Mission H — Conversation memory**
> "Implement conversation history storage (Postgres `messages` table) and context-aware query rewriting (FR-11/12/13) so a follow-up question is resolved against the prior turn before retrieval, without showing the rewritten query to the user."
- **Acceptance:** A scripted 2-turn conversation ('What is the scholarship deadline?' → '30 September' → 'What documents do I need?') returns an answer about scholarship documents, not a generic/ambiguous one.

**Mission I — Chat UI**
> "Build the React chat interface: message list, language indicator, inline source/citation display under each grounded answer, thumbs up/down feedback control, and a visibly distinct style for fallback ('couldn't find reliable information') messages. Wire it to `POST /api/v1/chat` and `POST /api/v1/feedback`."
- **Acceptance:** Manual E2E: user can chat, see sources rendered, and submit feedback that persists to Postgres.

**Mission J — Admin UI & analytics**
> "Build the admin UI: document upload with drag-and-drop, indexing-status view, approve/delete/version actions, unanswered-queries review list, and an analytics dashboard (FR-20/21/23) sourced from `GET /admin/analytics`."
- **Acceptance:** Admin can upload a document and watch it move through pending → approved → indexed in the UI, then confirm it's answerable in the chat UI.

**Mission K — Production hardening**
> "Add rate limiting on `/chat`, structured logging with a request/trace ID threaded through gateway → retrieval → LLM → response (Section 4 Observability), response caching for repeated identical queries, and finalize `docker-compose.yml` with restart policies for all services."
- **Acceptance:** Load test (k6/locust, 20 concurrent users) meets P95 ≤ 3.5s target; killing and letting Docker restart the backend container recovers automatically.

---

## 13. Suggested Antigravity Rules & Workflows

Create these as saved Antigravity **Rules** (persistent context) so every agent mission respects project conventions without repeating them each time:

- **Rule — Grounding discipline:** "Never let generated answer logic use unsupported model knowledge as a substitute for retrieved context. If context is insufficient, the code path must return the fallback response, never a best-guess answer."
- **Rule — Contract fidelity:** "All API request/response shapes must match `/contracts` exactly. If a change requires a contract change, update `/contracts` in the same task and flag it in the walkthrough."
- **Rule — Language neutrality:** "Do not hardcode English-only string matching for intent detection anywhere in the retrieval or language-understanding code paths."
- **Rule — No silent scope creep:** "Do not introduce a new library/technology not listed in Section 6 without calling it out explicitly in the task walkthrough with a one-line justification."

Create these as saved **Workflows** (multi-step `/workflow-name` slash commands) for repeatable processes:
- `/ingest-and-verify` — run the ingestion CLI on a given PDF, confirm it reaches `indexed` status, run one known-answer query against it, and report the answer + source in the walkthrough.
- `/run-eval-suite` — run the Section 10 evaluation scripts (retrieval metrics, faithfulness sample, fallback adversarial set, latency test) and produce a single summary report.

---

## 14. Open Questions / Assumptions (label clearly per project-context guidance)

These are **engineering assumptions**, not requirements from the official problem statement — confirm or override before/while building:
1. LLM provider/model for generation is not specified in the original form — assumed to be a Hugging Face-hosted or API-accessible model chosen for multilingual quality, latency, and cost; needs an explicit decision (see Roadmap Sprint 0).
2. Initial validated language set assumed as English, Hindi, Hinglish, +1 regional language (Odia, matching team context) — confirm against actual target user base.
3. Document formats assumed PDF-only for v1; DOCX/scanned-image OCR treated as post-MVP.
4. Hosting/deployment target (college server, cloud VM, etc.) not specified — Docker-first design keeps this decision deferrable.
