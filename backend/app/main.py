"""
PIM AI Coach — FastAPI application entrypoint.
"""

import logging
import os
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import setup_logging, generate_request_id, request_id_var

# Initialise structured logging before anything else
setup_logging()

# Optional Sentry integration — set PIM_SENTRY_DSN to enable
_sentry_dsn = os.environ.get("PIM_SENTRY_DSN", "")
if _sentry_dsn:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=0.1,
            environment=os.environ.get("RAILWAY_ENVIRONMENT", "production"),
        )
    except ImportError:
        pass  # sentry-sdk not installed — skip silently

from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router
from app.api.admin import router as admin_router
from app.api.stats import router as stats_router
from app.api.reindex import router as reindex_router
from app.api.country_profile import router as country_profile_router
from app.api.country_transparency import router as country_transparency_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PIM AI Coach",
    description="RAG-powered Public Investment Management coaching assistant",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Request-ID + timing middleware ───────────────────────────────────────────

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a unique request ID and log request duration."""

    async def dispatch(self, request: Request, call_next):
        rid = generate_request_id()
        request_id_var.set(rid)
        start = time.perf_counter()

        response: Response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Id"] = rid
        logger.info(
            "%s %s %s %.0fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


app.add_middleware(RequestContextMiddleware)


# ── Security headers middleware ──────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ── CORS ─────────────────────────────────────────────────────────────────────

_extra_origins = os.environ.get("PIM_CORS_ORIGINS", "")
_origins = ["http://localhost:3000", "http://localhost:3001"]
if _extra_origins:
    _origins.extend([o.strip() for o in _extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)


# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(chat_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(reindex_router, prefix="/api")
app.include_router(country_profile_router, prefix="/api")
app.include_router(country_transparency_router, prefix="/api")


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Basic health check — reports whether the app and database are reachable."""
    from app.config import settings
    status = {"app": "ok", "database": "unknown"}

    try:
        import psycopg
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        status["database"] = "ok"
    except Exception:
        status["database"] = "unreachable"

    overall = "ok" if status["database"] == "ok" else "degraded"
    return {"status": overall, **status}


# ── Graceful shutdown ────────────────────────────────────────────────────────

@app.on_event("shutdown")
async def shutdown():
    """Dispose of connection pools on shutdown."""
    try:
        from app.vectorstore.store import _get_pg_engine
        _get_pg_engine().dispose()
        logger.info("Database connection pool disposed")
    except Exception:
        pass
