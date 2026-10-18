# ─── Stage 1: Build & Dependencies ───────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Stage 2: Production Runtime ─────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /workspace

# Install minimal runtime dependencies: libpq5, tesseract OCR with language packs, curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-ori \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /install /usr/local

# Create non-root application user for production security compliance
RUN groupadd -g 10001 chatbot && \
    useradd -u 10001 -g chatbot -s /bin/bash -m chatbot

# Copy application source code
COPY . ./backend
RUN mkdir -p /workspace/backend/chroma_data /workspace/backend/uploads && \
    chown -R chatbot:chatbot /workspace

ENV PYTHONPATH=/workspace \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER chatbot
WORKDIR /workspace/backend

EXPOSE 8000

# Container healthcheck querying readiness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/readyz || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
