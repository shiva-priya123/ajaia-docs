from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.config import DEFAULT_JWT_SECRET, settings
from app.database import Base, SessionLocal, engine
from app.documents.router import router as documents_router
from app.seed import run_seed
from app.shares.router import router as shares_router
from app.upload.router import router as upload_router
from app.users.router import router as users_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create tables and seed demo data on startup."""
    import app.models  # noqa: F401  (register models on Base.metadata)

    if settings.JWT_SECRET == DEFAULT_JWT_SECRET:
        logger.warning("JWT_SECRET is using the default dev value — set it in production.")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()

    yield


application = FastAPI(
    title="Ajaia Collaborative Document Editor",
    version="1.0.0",
    lifespan=lifespan,
)

# Auth uses a Bearer header (not cookies), so credentials are not needed and
# origins can be an explicit allow-list.
application.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@application.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a consistent JSON error instead of a plain-text 500."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side. Please try again."})


@application.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness probe for the hosting platform."""
    return {"status": "ok"}


application.include_router(auth_router)
application.include_router(users_router)
application.include_router(documents_router)
application.include_router(shares_router)
application.include_router(upload_router)

# ── Serve the built frontend (production) ────────────────────────────────────
CLIENT_DIST = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "client", "dist"))

if os.path.isdir(CLIENT_DIST):
    assets_dir = os.path.join(CLIENT_DIST, "assets")
    if os.path.isdir(assets_dir):
        application.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @application.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> Response:
        """Serve the SPA's index.html for any non-API route (client-side routing)."""
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        file_path = os.path.realpath(os.path.join(CLIENT_DIST, full_path))
        # Path-traversal guard: only serve files that live inside dist/.
        if file_path.startswith(CLIENT_DIST + os.sep) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(CLIENT_DIST, "index.html"))
