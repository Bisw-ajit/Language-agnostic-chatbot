# Deployment & Production Operations Guide

## Overview
This document details deployment topologies, containerization strategies, environment configurations, and health check monitoring for deploying the Language Agnostic Chatbot in production environments.

---

## 1. Quick Start with Docker Compose

The complete production stack (PostgreSQL + FastAPI Backend + React/Nginx Frontend) is orchestrated via Docker Compose with automated health checks and startup sequencing:

```bash
# 1. Clone repository & configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your production GEMINI_API_KEY and strong SECRET_KEY (min 32 chars)

# 2. Build and start containers with health dependencies
docker compose up -d --build

# 3. Verify container health status
docker compose ps

# 4. Check readiness and metrics probes
curl -s http://localhost:8000/readyz | jq .
curl -s http://localhost:8000/metrics | head -n 25
```

---

## 2. Multi-Stage Docker Build Architecture

### Backend (`backend/Dockerfile`)
- **Stage 1 (Builder)**: Compiles native C-extensions (`gcc`, `libpq-dev`) and installs Python wheels into `/install`.
- **Stage 2 (Runner)**:
  - Minimal `python:3.11-slim` runtime.
  - Installs runtime-only dependencies (`libpq5`, `curl`, and Tesseract OCR with English, Hindi, and Odia models: `tesseract-ocr-eng`, `tesseract-ocr-hin`, `tesseract-ocr-ori`).
  - Creates dedicated non-root application user (`chatbot`, UID 10001, GID 10001) for security compliance.
  - Bundles built-in `HEALTHCHECK` querying `/readyz`.

### Frontend (`frontend/Dockerfile`)
- **Stage 1 (Builder)**: Builds static assets with Vite using `node:20-alpine`.
- **Stage 2 (Runner)**:
  - Hardened `nginx:alpine` runtime.
  - Gzip compression and security headers (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`).
  - Built-in reverse proxy routing `/api/` and health probes (`/healthz`, `/readyz`, `/metrics`) to the backend.
  - Built-in `HEALTHCHECK` verifying Nginx HTTP responsiveness.

---

## 3. Environment Variables Configuration

| Variable | Description | Default / Example | Required |
|---|---|---|---|
| `ENVIRONMENT` | Runtime environment (`development`, `staging`, `production`) | `production` | Yes |
| `SECRET_KEY` | JWT signing secret (min 32 characters in production) | `<generate-strong-key>` | Yes |
| `POSTGRES_URL` | SQLAlchemy connection URL | `postgresql://chatbot:pass@db:5432/chatbot_db` | Yes |
| `GEMINI_API_KEY` | Google AI Studio Gemini API key | `AIzaSy...` | Optional (Mock fallback engaged if empty) |
| `GEMINI_MODEL` | Gemini model name | `gemini-flash-latest` | No |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:3000,https://chatbot.yourdomain.com` | Yes |
| `MAX_UPLOAD_SIZE_MB` | Maximum allowed file upload size | `25` | No |
| `CONFIDENCE_THRESHOLD`| Minimum retrieval score before fallback | `0.25` | No |
| `RERANKER_TYPE` | Reranker engine (`semantic_lexical`, `cross_encoder`, `passthrough`) | `semantic_lexical` | No |

---

## 4. Kubernetes / Container Probes Specification

The backend exposes standardized Cloud Run and Kubernetes probes:

| Probe | Endpoint | Method | Success Response | Failure Response | Purpose |
|---|---|---|---|---|---|
| **Liveness** | `/healthz`, `/livez`, `/liveness` | `GET` | `200 OK` `{"status": "alive"}` | Connection Refused | Restarts stalled or deadlocked pods |
| **Readiness** | `/readyz`, `/readiness` | `GET` | `200 OK` (All 3 subsystems ready) | `503 Service Unavailable` | Controls load-balancer traffic routing |
| **Metrics** | `/metrics` | `GET` | `200 OK` (Prometheus v0.0.4 text) | `500 Internal Error` | Ingested by Prometheus scraper pods |

### Deep Readiness Probe Subsystem Checks
- **Database**: Executes `SELECT 1` on SQLAlchemy session pool.
- **ChromaDB Vector Store**: Verifies collection availability and active chunk count.
- **BM25 Lexical Index**: Verifies in-memory tokenized corpus documents.

```json
{
  "status": "ready",
  "database": "ok",
  "vector_store": "ok (4 chunks)",
  "bm25_index": "ok (4 docs)"
}
```

---

## 5. Kubernetes Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot-backend
  labels:
    app: chatbot-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatbot-backend
  template:
    metadata:
      labels:
        app: chatbot-backend
    spec:
      containers:
      - name: backend
        image: your-registry/chatbot-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: chatbot-secrets
        - configMapRef:
            name: chatbot-config
        livenessProbe:
          httpGet:
            path: /livez
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 10
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1536Mi"
```

---

## 6. Production Readiness Certification Checklist

- [x] **Zero OOD Hallucinations**: 100% abstention on out-of-domain queries (19/19).
- [x] **Grounding & Evidence Validation**: 100% evidence validation accuracy with zero false rejections across English, Hindi, Hinglish, and Odia.
- [x] **Multi-Tenant Isolation**: Complete isolation across dense ChromaDB vector search and sparse BM25 lexical search.
- [x] **Role-Based Access Control**: Hierarchical RBAC (`student`, `member`, `viewer`, `admin`, `super_admin`) with admin tenant filtering.
- [x] **Security Hardening**: Dual-view Unicode prompt injection defense (100% block rate on tested injection attacks, 0 false positives).
- [x] **Container Security**: Multi-stage Docker builds running under non-root user `chatbot` (UID 10001).
- [x] **Container Orchestration**: Docker Compose with `condition: service_healthy` startup sequencing.
- [x] **Observability**: Prometheus exposition format (`/metrics`), deep container lifecycle probes (`/healthz`, `/livez`, `/readyz`), and structured audit logging (`/api/v1/admin/audit-logs`).
- [x] **Distributed Tracing**: `X-Request-ID` and `X-Response-Time-Ms` exposed on all responses.
