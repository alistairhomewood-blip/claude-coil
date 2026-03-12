"""
FastAPI application entry point.

Phase 0: health endpoint only.
Phase 1 will register /api/stats, /api/discretise, etc.

Run in development:
    uvicorn api.main:app --reload --port 8000
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="coil-physics",
    description="Physics and compute backend for the coil geometry tool.",
    version="0.1.0",
)

# CORS — set ALLOWED_ORIGINS env var in production (comma-separated).
_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict:
    """Liveness check. Returns immediately with no dependencies."""
    return {"status": "ok"}
