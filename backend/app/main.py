"""
PIM AI Coach — FastAPI application entrypoint.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router
from app.api.admin import router as admin_router
from app.api.stats import router as stats_router
from app.api.reindex import router as reindex_router
from app.api.country_profile import router as country_profile_router

app = FastAPI(
    title="PIM AI Coach",
    description="RAG-powered Public Investment Management coaching assistant",
    version="0.1.0",
)

# Build CORS origins from env var + local defaults
_extra_origins = os.environ.get("PIM_CORS_ORIGINS", "")
_origins = ["http://localhost:3000", "http://localhost:3001"]
if _extra_origins:
    _origins.extend([o.strip() for o in _extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(reindex_router, prefix="/api")
app.include_router(country_profile_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
