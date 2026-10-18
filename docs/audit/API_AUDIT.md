# API Audit & Endpoint Inventory Report

**Project**: Language Agnostic Chatbot (SIH25104)  
**Audit Date**: October 2026  
**Auditor**: Senior Software Engineer & API Architect  
**Branch**: `audit/production-readiness`  

---

## 1. Executive Summary

This API audit evaluated all REST and streaming endpoints defined in the FastAPI application. Every route was inspected for HTTP semantics, request schema validation, response models, authentication and role-based access control (RBAC), error formatting consistency, CORS compliance, and health probe reliability.

---

## 2. Complete Endpoint Inventory

| HTTP Method | Route Path | Purpose | Authentication | Authorization Roles | Status Code(s) |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Student user registration | None (Public) | Anyone (Forces `student`) | `200`, `400` |
| `POST` | `/api/v1/auth/login` | User login (JSON or Form) | None (Public) | Any valid user | `200`, `400`, `401` |
| `POST` | `/api/v1/auth/create-admin` | Provision administrator | JWT Bearer | `admin`, `super_admin` | `200`, `400`, `401`, `403` |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile | JWT Bearer | Authenticated User | `200`, `401` |
| `POST` | `/api/v1/chat` | Synchronous unary RAG chat | JWT Bearer | `student`, `admin`, `super_admin` | `200`, `400`, `401`, `404` |
| `POST` | `/api/v1/chat/stream` | Real-time SSE token streaming chat | JWT Bearer | `student`, `admin`, `super_admin` | `200 (text/event-stream)`, `401` |
| `GET` | `/api/v1/conversations` | List user conversation history | JWT Bearer | Authenticated User | `200`, `401` |
| `GET` | `/api/v1/conversations/{id}/messages` | Get messages in conversation | JWT Bearer | Conversation Owner | `200`, `401`, `404` |
| `DELETE` | `/api/v1/conversations/{id}` | Delete conversation and messages | JWT Bearer | Conversation Owner | `200`, `401`, `404` |
| `POST` | `/api/v1/feedback` | Submit thumbs up/down message rating | JWT Bearer | Message / Conv Owner | `200`, `401`, `403`, `404` |
| `POST` | `/api/v1/admin/documents` | Upload, validate & ingest PDF scheme | JWT Bearer | `admin`, `super_admin` | `200`, `400`, `401`, `403`, `409`, `413` |
| `GET` | `/api/v1/admin/documents` | List uploaded documents with status | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403` |
| `GET` | `/api/v1/admin/documents/{id}/status` | Check asynchronous ingestion status | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403`, `404` |
| `PATCH` | `/api/v1/admin/documents/{id}` | Approve, reject, or archive document | JWT Bearer | `admin`, `super_admin` | `200`, `400`, `401`, `403`, `404` |
| `DELETE` | `/api/v1/admin/documents/{id}` | Purge document metadata and chunks | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403`, `404` |
| `GET` | `/api/v1/admin/analytics` | Aggregated analytics & queries | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403` |
| `GET` | `/api/v1/admin/unanswered-queries` | Review queries triggered fallback | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403` |
| `PATCH` | `/api/v1/admin/unanswered-queries/{id}` | Mark reviewed / add ground truth | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403`, `404` |
| `GET` | `/api/v1/admin/metrics` | Latency percentiles & pipeline stages | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403` |
| `GET` | `/api/v1/admin/users` | List tenant users and roles | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403` |
| `PATCH` | `/api/v1/admin/users/{id}/role` | Promote or demote user role | JWT Bearer | `super_admin` | `200`, `400`, `401`, `403`, `404` |
| `GET` | `/api/v1/admin/audit-logs` | Ingest and access security logs | JWT Bearer | `admin`, `super_admin` | `200`, `401`, `403` |
| `GET` | `/health`, `/healthz` | Basic process liveness probe | None (Public) | Public | `200` |
| `GET` | `/readyz`, `/readiness` | Deep dependency readiness probe | None (Public) | Public | `200` (Ready), `503` (Unready) |
| `GET` | `/livez`, `/liveness` | Container orchestration liveness | None (Public) | Public | `200` |
| `GET` | `/metrics` | Prometheus exposition metrics | None (Public) | Public | `200` (`text/plain`) |
| `GET` | `/docs`, `/redoc`, `/openapi.json` | OpenAPI documentation | None (Public) | Public | `200` |

---

## 3. Request Validation & Error Handling

### Standard Error Response Contract
All exceptions—whether raised by FastAPI, Starlette, or custom validation—are caught by global middleware and normalized into a consistent JSON envelope with tracing headers:

```json
{
  "detail": "Error description message",
  "error": {
    "code": 404,
    "message": "Error description message",
    "request_id": "4b684cb3-07ba-4648-9189-9a250393b584"
  },
  "request_id": "4b684cb3-07ba-4648-9189-9a250393b584"
}
```

### Response Headers Attached to Every Request
- `X-Request-ID`: Unique UUIDv4 assigned at ingress for distributed request tracing.
- `X-Response-Time-Ms`: High-precision latency recorded via `time.perf_counter()`.

---

## 4. Server-Sent Events (SSE) Streaming Protocol

The `/api/v1/chat/stream` endpoint streams responses using standard Server-Sent Events:

| Event Type | Payload Schema | Purpose |
|---|---|---|
| `event: status` | `{"stage": "retrieval", "conversation_id": "..."}` | Pipeline lifecycle updates |
| `event: token` | `{"token": "The"}` | Word-by-word streaming generation |
| `event: sources` | `[{"document_title": "...", "section": "...", "score": 0.85}]` | Verified evidence sources |
| `event: meta` | `{"confidence": 0.92, "detected_language": "or", "latency_ms": 32.5}` | Final response metadata |
| `event: done` | `{}` | End-of-stream signal |
| `event: error` | `{"detail": "..."}` | Graceful stream interruption |

---

## 5. Health, Readiness, and Liveness Probes

1. **Liveness Probe (`/livez` / `/liveness`)**:
   - Returns HTTP 200 `{"status": "alive"}` immediately. Used by Kubernetes/Docker/Render to determine whether the process is responsive.
2. **Readiness Probe (`/readyz` / `/readiness`)**:
   - Deep inspection:
     - Relational database: executes `SELECT 1`.
     - ChromaDB vector store: queries chunk collection count.
     - Okapi BM25 sparse index: verifies vocabulary and document corpus.
   - Returns HTTP 200 if all three systems are healthy; returns HTTP 503 if any system is disconnected or degraded.

---

## 6. Frontend Integration Alignment

- **API Client**: `frontend/src/api/client.js` uses an Axios client configured with `VITE_API_URL`.
- **JWT Handling**: Request interceptor attaches `Authorization: Bearer <token>`.
- **Session Expiry**: Response interceptor intercepts HTTP 401, flushes `localStorage`, and cleanly redirects to `/login?reason=session_expired` without infinite loops.
- **Error Normalization**: `getErrorMessage()` unpacks structured errors from `error.response.data.error.message` or FastAPI validation errors.
