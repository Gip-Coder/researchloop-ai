"""
Iteration repository for querying and persisting ResearchIterationModel.
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ResearchIterationModel


class IterationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, iteration: ResearchIterationModel) -> ResearchIterationModel:
        self.session.add(iteration)
        await self.session.commit()
        await self.session.refresh(iteration)
        return iteration

    async def get_by_run_id(self, run_id: str) -> List[ResearchIterationModel]:
        stmt = (
            select(ResearchIterationModel)
            .where(ResearchIterationModel.run_id == run_id)
            .order_by(ResearchIterationModel.iteration_number.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
