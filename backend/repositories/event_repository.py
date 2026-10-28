"""
Event repository for persisting and querying telemetry and AgentEvent traces.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import AgentEventModel


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event: AgentEventModel) -> AgentEventModel:
        self.session.add(event)
        await self.session.commit()
        return event

    async def create_many(self, events: List[AgentEventModel]) -> List[AgentEventModel]:
        self.session.add_all(events)
        await self.session.commit()
        return events

    async def get_by_run_id(
        self,
        run_id: str,
        after_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[AgentEventModel]:
        stmt = (
            select(AgentEventModel)
            .where(AgentEventModel.run_id == run_id)
            .order_by(AgentEventModel.timestamp.asc())
            .limit(limit)
        )
        if after_id:
            # Subquery or filter by timestamp of after_id
            cursor_stmt = select(AgentEventModel.timestamp).where(AgentEventModel.id == after_id)
            cursor_res = await self.session.execute(cursor_stmt)
            cursor_time = cursor_res.scalar_one_or_none()
            if cursor_time:
                stmt = stmt.where(AgentEventModel.timestamp > cursor_time)

        res = await self.session.execute(stmt)
        return list(res.scalars().all())
