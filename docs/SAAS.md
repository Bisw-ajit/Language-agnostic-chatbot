# SaaS Architecture & Multi-Tenancy Design

## Overview
The Language Agnostic Chatbot is structured as a B2B / B2G multi-tenant Software-as-a-Service (SaaS) platform, enabling multiple government departments, districts, or educational institutions to operate isolated RAG assistants on a shared infrastructure footprint.

---

## 1. Multi-Tenant Model: Shared Database with Tenant Scoping

We employ a **Shared Database, Shared Schema** architecture with strict logical tenant partitioning:

| Layer | Isolation Mechanism |
|---|---|
| **API Layer** | User identity & tenant resolved from JWT claims (`user.tenant_id`) |
| **Relational Database** | All queries enforce `WHERE tenant_id = :tenant_id` filter |
| **Vector Database** | ChromaDB queries enforce `{"$and": [{"tenant_id": "..."}, ...]}` metadata filter |
| **Document Storage** | Uploaded files prefixed with UUIDs, stored in separate tenant-scoped records |
| **Analytics & Metrics** | Metrics endpoints group and report by tenant |

---

## 2. Tenant Lifecycle Management

1. **Organization Onboarding**:
   - Seeded default tenant: `default-tenant` ("Department of Agriculture and Farmers Empowerment").
   - Additional tenants are provisioned via `Organization` records with unique `slug` identifiers.
2. **User Assignment**:
   - Users are bound to a single tenant upon creation.
   - Self-registered public users are assigned to the default institutional tenant.
3. **Document Ingestion per Tenant**:
   - Institutional administrators upload scheme PDFs into their tenant workspace.
   - Document approval automatically archives older active versions within the same tenant only, preventing cross-tenant policy interference.

---

## 3. Observability & SaaS Metrics

- **Ring-Buffer Latency Tracker**: The backend maintains an in-memory ring buffer of the last 1,000 requests, calculating rolling P50, P95, and P99 latencies for each pipeline stage (`retrieval`, `rerank`, `validation`, `llm`, `total`).
- **Telemetry Endpoints**:
  - `GET /api/v1/admin/analytics`: Real-time tenant-level volume, conversation counts, and fallback rates.
  - `GET /api/v1/admin/metrics`: Real-time latency percentiles for SLA monitoring.
- **Request Tracing**: `X-Request-ID` and `X-Response-Time-Ms` headers on every response enable end-to-end distributed tracing across microservices and reverse proxies.
