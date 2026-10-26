"""FastAPI application entry point.

Run locally with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from app.webhook.router import router as webhook_router

app = FastAPI(title="GitHub Actions Security Fixer", version="0.1.0")
app.include_router(webhook_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
