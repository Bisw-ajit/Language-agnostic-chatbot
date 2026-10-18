# REST & Streaming API Reference

## Base URL
- Local: `http://localhost:8000/api/v1`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

## 1. Authentication Endpoints

### Register User
- **Method**: `POST /api/v1/auth/register`
- **Auth**: None
- **Body**:
  ```json
  {
    "email": "user@domain.com",
    "password": "SecurePassword123"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "<jwt-token>",
    "token_type": "bearer",
    "role": "student",
    "user_id": "<uuid>"
  }
  ```
  *Note: Client-supplied roles in registration are strictly overridden to `"student"`.*

### Login
- **Method**: `POST /api/v1/auth/login`
- **Auth**: None
- **Body**:
  ```json
  {
    "email": "user@domain.com",
    "password": "SecurePassword123"
  }
  ```
- **Response**: `200 OK` (returns JWT, role, user_id)

### Create Admin (Privileged)
- **Method**: `POST /api/v1/auth/create-admin`
- **Auth**: Bearer JWT (`admin` or `super_admin`)
- **Body**:
  ```json
  {
    "email": "admin2@domain.com",
    "password": "AdminPassword123"
  }
  ```

---

## 2. Chat & RAG Endpoints

### Send Chat Message (Standard)
- **Method**: `POST /api/v1/chat`
- **Auth**: Bearer JWT
- **Body**:
  ```json
  {
    "message": "What is the assistance amount under KALIA yojana?",
    "conversation_id": "<optional-uuid>",
    "preferred_language": "en"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "conversation_id": "<uuid>",
    "message_id": "<uuid>",
    "answer": "Under the KALIA scheme, eligible farmers receive ₹10,000 per year in two equal installments...",
    "sources": [
      {
        "document_id": "<uuid>",
        "document_title": "KALIA Scheme Guidelines",
        "section": "Financial Benefits",
        "score": 0.88,
        "excerpt": "..."
      }
    ],
    "detected_language": "en",
    "language_display": "English",
    "confidence": 0.885,
    "evidence_level": "HIGH",
    "is_fallback": false,
    "llm_status": "LLM_SUCCESS",
    "generation_source": "gemini",
    "latency_ms": {
      "retrieval": 12.4,
      "rerank": 4.1,
      "validation": 0.8,
      "llm": 1250.3,
      "total": 1267.6
    }
  }
  ```

### Stream Chat Message (Server-Sent Events)
- **Method**: `POST /api/v1/chat/stream`
- **Auth**: Bearer JWT
- **Header**: `Accept: text/event-stream`
- **Events Emitted**:
  - `status`: Pipeline phase (`retrieval`, `generating`)
  - `token`: Individual tokens (`{"token": "Under"}`)
  - `sources`: Complete list of evidence chunks
  - `meta`: Language, confidence, latency, LLM status
  - `done`: End of stream marker

---

## 3. Conversations & Feedback

- `GET /api/v1/conversations`: List conversations for the logged-in user.
- `GET /api/v1/conversations/{id}/messages`: Retrieve full turn-by-turn history.
- `DELETE /api/v1/conversations/{id}`: Delete conversation and associated messages.
- `POST /api/v1/feedback`: Submit `up` or `down` rating and optional comment.

---

## 4. Admin Management Endpoints

- `POST /api/v1/admin/documents`: Multipart upload PDF (scanned/text) for ingestion.
- `GET /api/v1/admin/documents`: List uploaded documents scoped to admin's tenant.
- `PATCH /api/v1/admin/documents/{id}`: Approve (`active`) or archive (`archived`) document.
- `DELETE /api/v1/admin/documents/{id}`: Purge document and delete vector embeddings.
- `GET /api/v1/admin/analytics`: Tenant-isolated analytics (fallback rate, total messages).
- `GET /api/v1/admin/metrics`: P50 / P95 / P99 latency percentiles for RAG pipeline.
- `GET /api/v1/admin/users`: List users in tenant.
- `PATCH /api/v1/admin/users/{id}/role`: Promote or update user roles.

---

## 5. System Probes

- `GET /health`: Basic health and version status.
- `GET /readiness`: Database accessibility verification (`200` or `503`).
- `GET /liveness`: Application container heartbeat (`200`).
