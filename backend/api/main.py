"""
Main FastAPI application for researchloop-ai.
Integrates API routes, CORS, database lifecycle, and static frontend hosting.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import health, research
from backend.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ResearchLoop AI — Application API",
        description="Autonomous literature review agent pipeline API with iterative planning, retrieval, synthesis, and self-reflection.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    allowed_origins_raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
    )
    allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]
    if "*" not in allowed_origins:
        allowed_origins.append("http://localhost:3000")
        allowed_origins.append("http://localhost:5173")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if "*" not in allowed_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(health.router, prefix="/api")
    app.include_router(research.router, prefix="/api")

    # Static frontend files support (if frontend is built)
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api"):
                return None
            target_file = frontend_dist / full_path
            if target_file.is_file():
                return FileResponse(str(target_file))
            return FileResponse(str(frontend_dist / "index.html"))

    return app


app = create_app()
