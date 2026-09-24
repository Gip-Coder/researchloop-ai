"""
Health and operational readiness route.
"""

from __future__ import annotations

from fastapi import APIRouter
from backend.agent.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service health check")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "researchloop-ai",
        "version": "0.1.0",
        "mode": settings.researchloop_mode,
        "is_mock_mode": settings.is_mock_mode,
        "llm_provider": settings.llm_provider,
    }
