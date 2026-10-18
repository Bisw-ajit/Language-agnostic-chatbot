import uuid
import time
import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.models.database import create_tables, seed_demo_users
from backend.auth.router import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.admin import router as admin_router
from backend.rag.vector_store import sync_bm25_from_chroma
from backend.observability import record_http_request, export_prometheus_text

# ─── Structured Logging Configuration ─────────────────────────────────────────
settings = get_settings()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "logging.Formatter",
            "fmt": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
        },
        "standard": {
            "format": "[%(asctime)s] %(levelname)s %(name)s — %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if settings.environment in ("production", "staging") else "standard",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "uvicorn.access": {"handlers": ["console"], "propagate": False, "level": "WARNING"},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("chatbot.main")

# ─── Production Secret Key Guard ───────────────────────────────────────────────
if settings.environment == "production":
    if settings.secret_key in [
        "super-secret-jwt-key-change-in-production", "secret", "change-this-in-production"
    ] or len(settings.secret_key) < 32:
        raise RuntimeError(
            "FATAL: Insecure or default SECRET_KEY detected in production environment. "
            "A strong key of at least 32 characters is required."
        )

# ─── Application Lifespan ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Language Agnostic Chatbot API", extra={"environment": settings.environment})
    create_tables()
    if settings.environment != "production":
        seed_demo_users()
        logger.info("Non-production environment: demo users seeded")
    else:
        logger.info("Production environment: automatic demo user seeding skipped for security")
    sync_bm25_from_chroma()
    logger.info("Startup complete — database tables verified, BM25 index synced")
    yield
    logger.info("Shutting down Language Agnostic Chatbot API")

# ─── App Initialization ────────────────────────────────────────────────────────
app = FastAPI(
    title="Language Agnostic Chatbot API",
    version="2.0.0",
    description="SaaS-grade multilingual RAG system for Odisha government schemes",
    lifespan=lifespan,
)

from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

# ─── Request ID + Latency + Metrics Middleware ─────────────────────────────────
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Injects request_id, logs request, and updates Prometheus metrics."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.exception(f"Unhandled server error [request_id={request_id}]: {exc}")
        record_http_request(request.method, request.url.path, 500)
        return JSONResponse(
            status_code=500,
            headers={
                "X-Request-ID": request_id,
                "X-Response-Time-Ms": str(latency_ms),
            },
            content={
                "detail": "Internal server error occurred. Please contact system administrator.",
                "error": {
                    "code": 500,
                    "message": "Internal server error occurred. Please contact system administrator.",
                    "request_id": request_id,
                },
                "request_id": request_id,
            },
        )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(latency_ms)

    # Record Prometheus metrics
    record_http_request(request.method, request.url.path, response.status_code)

    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({latency_ms}ms)",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        },
    )
    return response

# ─── CORS Middleware (Wrapped outermost to guarantee headers on all responses) ───
cors_origins = settings.cors_origins_list
allow_credentials = True
if "*" in cors_origins:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
)

# ─── Standardized Exception Handlers ───────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    detail = exc.detail
    message = detail if isinstance(detail, str) else str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        headers={"X-Request-ID": request_id, **(getattr(exc, "headers", None) or {})},
        content={
            "detail": detail,
            "error": {
                "code": exc.status_code,
                "message": message,
                "request_id": request_id,
            },
            "request_id": request_id,
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    loc = " -> ".join(str(l) for l in first_error.get("loc", []))
    msg = first_error.get("msg", "Invalid request parameter")
    summary = f"Validation error at {loc}: {msg}" if loc else f"Validation error: {msg}"
    return JSONResponse(
        status_code=422,
        headers={"X-Request-ID": request_id},
        content={
            "detail": errors,
            "error": {
                "code": 422,
                "message": summary,
                "request_id": request_id,
                "details": errors,
            },
            "request_id": request_id,
        },
    )

# ─── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)

# ─── Health / Readiness / Liveness Probes ──────────────────────────────────────
@app.get("/health", tags=["infra"])
@app.get("/healthz", tags=["infra"])
def health_check():
    """Basic health — always returns 200 if process is alive."""
    return {"status": "ok", "version": "2.0.0", "environment": settings.environment}


@app.get("/readiness", tags=["infra"])
@app.get("/readyz", tags=["infra"])
def readiness_check():
    """
    Readiness probe — verifies relational database, ChromaDB, and BM25 index.
    Returns 200 if ready to serve traffic, 503 if any dependency is unavailable.
    """
    from backend.models.database import SessionLocal
    from backend.rag.vector_store import get_or_create_collection
    from backend.rag.bm25 import get_bm25_index
    from sqlalchemy import text

    checks = {"database": "unknown", "vector_store": "unknown", "bm25_index": "unknown"}
    all_ready = True

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as e:
        logger.error(f"Readiness check failed (database): {e}")
        checks["database"] = f"error: {str(e)}"
        all_ready = False

    try:
        col = get_or_create_collection("documents")
        chunk_count = col.count()
        checks["vector_store"] = f"ok ({chunk_count} chunks)"
    except Exception as e:
        logger.error(f"Readiness check failed (vector_store): {e}")
        checks["vector_store"] = f"error: {str(e)}"
        all_ready = False

    try:
        bm25 = get_bm25_index()
        checks["bm25_index"] = f"ok ({bm25.corpus_size} docs)"
    except Exception as e:
        logger.error(f"Readiness check failed (bm25_index): {e}")
        checks["bm25_index"] = f"error: {str(e)}"
        all_ready = False

    if all_ready:
        return {"status": "ready", **checks}
    else:
        return JSONResponse(status_code=503, content={"status": "not_ready", **checks})


@app.get("/liveness", tags=["infra"])
@app.get("/livez", tags=["infra"])
def liveness_check():
    """
    Liveness probe — always returns 200 as long as the process is running.
    Kubernetes / Cloud Run use this to know whether to restart the container.
    """
    return {"status": "alive"}


@app.get("/metrics", tags=["infra"])
def prometheus_metrics():
    """Prometheus exposition metrics endpoint for scraper pods."""
    return Response(
        content=export_prometheus_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )
