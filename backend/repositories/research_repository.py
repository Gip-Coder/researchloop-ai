"""
Research repository for database operations on ResearchRunModel.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    ResearchRunModel,
    ResearchIterationModel,
    ResearchRunPaperModel,
    ThemeModel,
    AgentEventModel,
)


class ResearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, run: ResearchRunModel) -> ResearchRunModel:
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_by_id(self, run_id: str) -> Optional[ResearchRunModel]:
        stmt = (
            select(ResearchRunModel)
            .where(ResearchRunModel.id == run_id)
            .options(
                selectinload(ResearchRunModel.iterations),
                selectinload(ResearchRunModel.run_papers).joinedload(ResearchRunPaperModel.paper),
                selectinload(ResearchRunModel.themes),
                selectinload(ResearchRunModel.events),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_runs(self, limit: int = 50, offset: int = 0) -> List[ResearchRunModel]:
        stmt = (
            select(ResearchRunModel)
            .order_by(desc(ResearchRunModel.created_at))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(ResearchRunModel.iterations),
                selectinload(ResearchRunModel.run_papers),
                selectinload(ResearchRunModel.themes),
            )
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_status(
        self,
        run_id: str,
        status: str,
        current_iteration: Optional[int] = None,
        coverage: Optional[float] = None,
        stopping_reason: Optional[str] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[ResearchRunModel]:
        run = await self.session.get(ResearchRunModel, run_id)
        if not run:
            return None
        run.status = status
        run.updated_at = datetime.now(timezone.utc)
        if current_iteration is not None:
            run.current_iteration = current_iteration
        if coverage is not None:
            run.coverage = coverage
        if stopping_reason is not None:
            run.stopping_reason = stopping_reason
        if error is not None:
            run.error = error
        if started_at is not None:
            run.started_at = started_at
        if completed_at is not None:
            run.completed_at = completed_at
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def save_final_result(
        self,
        run_id: str,
        status: str,
        final_review: Optional[dict[str, Any]],
        synthesis: Optional[dict[str, Any]],
        reflection: Optional[dict[str, Any]],
        evaluation: Optional[dict[str, Any]],
        metadata: Optional[dict[str, Any]],
        coverage: float,
        stopping_reason: Optional[str],
        completed_at: Optional[datetime] = None,
        error: Optional[str] = None,
    ) -> Optional[ResearchRunModel]:
        run = await self.session.get(ResearchRunModel, run_id)
        if not run:
            return None
        run.status = status
        run.final_review = final_review
        run.synthesis = synthesis
        run.reflection = reflection
        run.evaluation = evaluation
        run.metadata_json = metadata
        run.coverage = coverage
        run.stopping_reason = stopping_reason
        if error is not None:
            run.error = error
        run.completed_at = completed_at or datetime.now(timezone.utc)
        run.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(run)
        return run
