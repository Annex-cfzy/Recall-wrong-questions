"""FastAPI application entrypoint.

Registers routers, exception handlers, CORS, and initialises the database on
startup. Routers are added incrementally per milestone.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api import notebooks, errors, review, chat, dashboard, export, upgrade
from app.core.config import BASE_DIR

import os
from fastapi.responses import FileResponse

app = FastAPI(
    title="Recall — AI 智能错题本",
    description="Local-first AI error notebook API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(ValueError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(notebooks.router)
app.include_router(errors.router)
app.include_router(review.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(export.router)
app.include_router(upgrade.router)

@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    return {"code": 0, "message": "success", "data": {"status": "ok"}}


# In production (frontend built into ../frontend/dist), serve the SPA from
# FastAPI itself. In development the dist folder is absent, so the Vite dev
# server (port 5173) is used instead and this block is skipped.
# This catch-all GET route is registered LAST so every explicit /api/* route
# (and /docs, /openapi.json) registered above matches first; only unmatched
# paths fall through to the SPA (with index.html fallback for client routing).
# In production the built SPA is served by FastAPI itself. The dist may live
# either alongside the backend (../frontend/dist — local dev & Docker image) or
# embedded inside the backend package (frontend/dist — FC code-package deploy).
# Prefer the embedded copy when present so a single zip serves both API and SPA.
_EMBEDDED_DIST = os.path.normpath(os.path.join(str(BASE_DIR), "frontend", "dist"))
_STANDALONE_DIST = os.path.normpath(os.path.join(str(BASE_DIR), "..", "frontend", "dist"))
_FRONTEND_DIST = _EMBEDDED_DIST if os.path.isdir(_EMBEDDED_DIST) else _STANDALONE_DIST
if os.path.isdir(_FRONTEND_DIST):

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        candidate = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))
