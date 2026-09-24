"""
Theme repository for managing extracted research themes.
"""

from __future__ import annotations

import uuid
from typing import List, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ThemeModel


class ThemeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_theme(
        self,
        run_id: str,
        theme_id: str,
        title: str,
        description: str,
        paper_ids: list[str],
        key_findings: list[str],
        contradictions_or_tensions: list[str],
    ) -> ThemeModel:
        theme = ThemeModel(
            id=str(uuid.uuid4()),
            run_id=run_id,
            theme_id=theme_id,
            title=title,
            description=description,
            paper_ids=paper_ids,
            key_findings=key_findings,
            contradictions_or_tensions=contradictions_or_tensions,
        )
        self.session.add(theme)
        await self.session.flush()
        return theme

    async def get_by_run_id(self, run_id: str) -> List[ThemeModel]:
        stmt = (
            select(ThemeModel)
            .where(ThemeModel.run_id == run_id)
            .order_by(ThemeModel.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
