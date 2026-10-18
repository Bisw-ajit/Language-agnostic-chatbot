# Database Architecture & Migration Guide

## Overview
The application uses SQLAlchemy ORM with support for SQLite (development/testing) and PostgreSQL (production). Connection pooling, optimistic locking, cascade deletion, and timezone-aware timestamps are configured across all tables.

---

## 1. Schema Diagram & Relationships

```
                  ┌──────────────────────┐
                  │    organizations     │
                  │ (tenant isolation)   │
                  └──────────┬───────────┘
                             │ 1:N
            ┌────────────────┼────────────────┬────────────────┐
            ▼                ▼                ▼                ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
     │    users    │  │conversations│  │  documents  │  │  analytics   │
     └──────┬──────┘  └──────┬──────┘  └─────────────┘  └──────────────┘
            │                │ 1:N
            │                ▼
            │         ┌─────────────┐
            └────────>│  messages   │
                      └──────┬──────┘
                             │ 1:1
                             ▼
                      ┌─────────────┐
                      │  feedback   │
                      └─────────────┘
```

---

## 2. Table Specifications

### `organizations`
- `id`: Primary key (UUID string)
- `name`: Organization / Department name (e.g. "Department of Agriculture & Farmers' Empowerment")
- `slug`: URL-friendly identifier (e.g. "odisha-agri")
- `created_at`: Creation timestamp (UTC)

### `users`
- `id`: Primary key (UUID string)
- `tenant_id`: Foreign key to `organizations.id` (Indexed)
- `email`: User email address (Unique, Indexed)
- `hashed_password`: Passlib PBKDF2-SHA256 password hash
- `role`: Role enum (`student`, `admin`, `super_admin`)
- `created_at`: Creation timestamp (UTC)

### `conversations`
- `id`: Primary key (UUID string)
- `tenant_id`: Foreign key to `organizations.id` (Indexed)
- `user_id`: Foreign key to `users.id`
- `created_at` / `updated_at`: UTC timestamps

### `messages`
- `id`: Primary key (UUID string)
- `conversation_id`: Foreign key to `conversations.id` (Cascade delete)
- `role`: `user` or `assistant`
- `content`: Text content
- `detected_language`: Detected language code (`en`, `hi`, `hi-en`, `or`)
- `confidence_score`: Retrieval composite confidence score
- `is_fallback`: Boolean indicating if answer was a deterministic fallback
- `created_at`: UTC timestamp

### `feedback`
- `id`: Primary key (UUID string)
- `message_id`: Foreign key to `messages.id` (Unique, Cascade delete)
- `rating`: `up` or `down`
- `comment`: Optional user commentary
- `created_at`: UTC timestamp

### `document_metadata`
- `id`: Primary key (UUID string)
- `tenant_id`: Foreign key to `organizations.id` (Indexed)
- `title` / `filename`: Document title and physical file name
- `department` / `category` / `language` / `version`: Administrative metadata
- `status`: Lifecycle state (`pending`, `active`, `archived`)
- `checksum`: SHA-256 binary hash for deduplication
- `uploaded_by`: Foreign key to `users.id`

---

## 3. Production Connection Pooling

For PostgreSQL environments, `backend/models/database.py` enables production-grade connection pooling:
```python
engine = create_engine(
    settings.postgres_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,    # Tests connections before checkout (eliminates stale connections)
    pool_recycle=1800      # Recycles connections every 30 minutes
)
```

---

## 4. Alembic Migrations

Migrations are stored in `backend/alembic/versions/`:
- `46311d3c5254_initial_saas_multi_tenant_schema.py`: Establishes organizations, tenant foreign keys, batch constraints for SQLite compatibility, and indexes.
