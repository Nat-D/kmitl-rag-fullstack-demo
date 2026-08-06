"""FastAPI entry point.

Wires the two routers under /api, exposes /api/health and /api/config, and — if a
built frontend is present — serves the Svelte SPA so the whole app is one URL.

Read order for the app: config -> database -> models -> schemas -> chunking/llm
-> repositories -> services -> routers -> main. (See the README's reading guide.)
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import chat, documents

app = FastAPI(title="KMITL RAG demo", version="1.0.0")

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
async def config() -> dict[str, object]:
    """Non-secret knobs, shown in the UI so students can see the settings that
    drive retrieval. Never exposes the API key."""
    return {
        "chat_model": settings.chat_model,
        "embed_model": settings.embed_model,
        "embed_dim": settings.embed_dim,
        "top_k": settings.top_k,
        "min_score": settings.min_score,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }


# ---- serve the built Svelte SPA (optional; present in the Docker image) ----
_STATIC_DIR = Path(os.environ.get("STATIC_DIR", "frontend_build"))
if _STATIC_DIR.is_dir():
    app_assets = _STATIC_DIR / "_app"
    if app_assets.is_dir():
        app.mount("/_app", StaticFiles(directory=app_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        # Serve a real file if it exists (favicon, etc.), else the SPA shell so
        # client-side routing (/, /ask) works on refresh.
        candidate = _STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC_DIR / "index.html")
