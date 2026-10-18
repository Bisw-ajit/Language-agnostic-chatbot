# Security Architecture & Hardening Guide

## Overview
This document outlines the end-to-end security architecture of the Language Agnostic Chatbot SaaS platform (SIH25104). The application has been hardened against common web application vulnerabilities (OWASP Top 10), adversarial prompt injection, multi-tenant data leakage, and malicious document uploads.

---

## 1. Authentication & Authorization

### Role-Based Access Control (RBAC)
The platform enforces three distinct security roles:
- **`student`**: Default citizen/student user. Can chat, start conversations, view their own message history, and submit feedback. Cannot access any admin APIs.
- **`admin`**: Institutional administrator. Can upload, approve, archive, and delete official scheme documents for their organization, view analytics, and manage users within their tenant.
- **`super_admin`**: Platform-wide administrator with cross-tenant visibility.

### Privilege Escalation Prevention
- **Registration Hardening**: The public `/api/v1/auth/register` endpoint strictly enforces `role = "student"`. Any client-supplied `role` field in the registration payload is completely ignored server-side.
- **Admin Provisioning Guard**: Administrator creation is restricted to the `/api/v1/auth/create-admin` endpoint, which is protected by JWT authentication requiring `require_role("admin", "super_admin")`.
- **Frontend Safety**: Role selection dropdowns have been removed from the public registration UI to prevent client confusion.

### JWT Token Security
- **Algorithm**: HS256 with strong signature verification.
- **Secret Key Validation**: At application startup in `production` mode, `backend/main.py` enforces that `SECRET_KEY` is not a default/insecure value and has a minimum length of 32 characters, terminating immediately if insecure.
- **UTC Timestamps**: Token expiration (`exp`) and issued-at (`iat`) use timezone-aware UTC datetime (`datetime.now(timezone.utc)`), preventing clock skew vulnerabilities.

---

## 2. Multi-Tenant Isolation

### Relational Database Isolation
- Every database model (`User`, `Conversation`, `DocumentMetadata`, `AnalyticsDaily`) carries a mandatory `tenant_id` foreign key referencing `organizations.id`.
- All database queries in `/api/v1/chat`, `/api/v1/conversations`, and `/api/v1/admin/*` are scoped to `current_user.tenant_id`.
- Super administrators can optionally query cross-tenant resources.

### Vector Store (ChromaDB) Isolation
- All chunk embeddings stored in ChromaDB carry `tenant_id` in their metadata payload.
- Retrieval queries via `vector_search(query, top_k, tenant_id=...)` construct a boolean `$and` where-clause:
  ```json
  {"$and": [{"status": "active"}, {"tenant_id": "tenant-xyz"}]}
  ```
- This guarantees vector-level isolation even in a shared vector database collection.

---

## 3. Document Upload Security & Ingestion Guardrails

File uploads via `/api/v1/admin/documents` undergo strict 6-stage validation:
1. **Filename Extension**: Only `.pdf` (case-insensitive) is permitted.
2. **MIME Type Inspection**: Must match `application/pdf` or `application/x-pdf`.
3. **Empty File & Size Bounds**: Rejects 0-byte files; enforces configurable `MAX_UPLOAD_SIZE_MB` (default 25 MB).
4. **Magic Byte Verification**: File must begin with the binary header `%PDF` (`0x25 0x50 0x44 0x46`).
5. **PyMuPDF Document Integrity & Encryption Check**: Rejects password-protected or corrupt PDFs, and PDFs with 0 pages.
6. **Path Traversal & Sanitization**: Filenames are sanitized via regex `[^a-zA-Z0-9._-]` and prefixed with UUIDs, ensuring destination paths remain inside `UPLOAD_DIR`.
7. **SHA-256 Checksum Deduplication**: Duplicate documents matching active records are rejected with `409 Conflict`.

---

## 4. Prompt Injection Defense

Adversarial queries are intercepted by `backend/rag/injection_guard.py` before reaching retrieval or the LLM:
- **Jailbreak Detection**: Blocks DAN mode, unrestricted persona requests, and developer mode switches.
- **Role Override**: Blocks phrases like `ignore all previous instructions` and `disregard all rules`.
- **System Prompt Exfiltration**: Intercepts requests attempting to extract base instructions or prompts.
- **Template Boundary Escapes**: Neutralizes Markdown/chat template tokens (`<|im_start|>`, `### SYSTEM ###`).
- **Unicode Sanitization**: Strips zero-width characters and normalizes homoglyphs via NFKC.
- **Rejection Behavior**: Blocked queries immediately return a deterministic response (`llm_status: "BLOCKED_INJECTION"`) without invoking LLM providers.

---

## 5. Network & Infrastructure Security

- **CORS Configuration**: Explicit origin whitelisting via `CORS_ORIGINS` environment variable. Wildcard `*` origins with credentials are expressly prohibited.
- **Request Tracing**: Every inbound HTTP request receives a unique UUID `X-Request-ID` and `X-Response-Time-Ms` response header.
- **Credential Storage**: Sensitive API keys and connection strings are strictly loaded via `.env` and excluded from source control via `.gitignore`.
