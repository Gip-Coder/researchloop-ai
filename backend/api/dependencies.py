"""
FastAPI dependency injection utilities.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.services.research_service import ResearchService


async def get_research_service(
    session: AsyncSession = Depends(get_db),
) -> ResearchService:
    """Dependency providing a ResearchService instance bound to the request's DB session."""
    return ResearchService(session)
