"""
Application service coordinating research workflows, queries, and execution.
"""

from __future__ import annotations

import uuid
from typing import Any, List, Optional, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import (
    AgentEventModel,
    PaperModel,
    ResearchIterationModel,
    ResearchRunModel,
    ResearchRunPaperModel,
    ThemeModel,
)
from backend.repositories.event_repository import EventRepository
from backend.repositories.iteration_repository import IterationRepository
from backend.repositories.paper_repository import PaperRepository
from backend.repositories.research_repository import ResearchRepository
from backend.repositories.theme_repository import ThemeRepository
from backend.services.research_runner import ResearchRunner


class ResearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.research_repo = ResearchRepository(session)
        self.iteration_repo = IterationRepository(session)
        self.paper_repo = PaperRepository(session)
        self.theme_repo = ThemeRepository(session)
        self.event_repo = EventRepository(session)

    async def create_research_run(
        self,
        research_question: str,
        config: Optional[Any] = None,
    ) -> ResearchRunModel:
        """Create a new research run in pending status."""
        if hasattr(config, "model_dump"):
            config_dict = config.model_dump()
        elif isinstance(config, dict):
            config_dict = config
        else:
            config_dict = {}
        max_iters = config_dict.get("max_iterations", 3)

        run = ResearchRunModel(
            id=str(uuid.uuid4()),
            research_question=research_question.strip(),
            status="pending",
            max_iterations=max_iters,
            coverage=0.0,
            config=config_dict,
        )
        return await self.research_repo.create(run)

    async def start_research_run(self, run_id: str) -> None:
        """Dispatch asynchronous background execution of the research run."""
        await ResearchRunner.run_in_background(run_id)

    async def get_research_run(self, run_id: str) -> Optional[ResearchRunModel]:
        """Fetch research run by id."""
        return await self.research_repo.get_by_id(run_id)

    async def list_runs(self, limit: int = 50, offset: int = 0) -> List[ResearchRunModel]:
        """List historical research runs ordered by recency."""
        return await self.research_repo.list_runs(limit=limit, offset=offset)

    async def delete_research_run(self, run_id: str) -> bool:
        """Delete a single research run from history and database."""
        return await self.research_repo.delete(run_id)

    async def clear_all_research_runs(self) -> int:
        """Delete all research runs from history and database."""
        return await self.research_repo.delete_all()

    async def get_iterations(self, run_id: str) -> List[ResearchIterationModel]:
        """Fetch audit log iterations for a research run."""
        return await self.iteration_repo.get_by_run_id(run_id)

    async def get_papers(
        self,
        run_id: str,
        is_relevant: Optional[bool] = None,
        source: Optional[str] = None,
        min_relevance: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "relevance",
    ) -> List[Tuple[PaperModel, ResearchRunPaperModel]]:
        """Fetch papers with criteria-based filtering and sorting."""
        return await self.paper_repo.get_papers_for_run(
            run_id=run_id,
            is_relevant=is_relevant,
            source=source,
            min_relevance=min_relevance,
            search=search,
            sort_by=sort_by,
        )

    async def get_events(
        self,
        run_id: str,
        after_id: Optional[str] = None,
        limit: int = 500,
    ) -> List[AgentEventModel]:
        """Fetch event trace for live progress and timeline rendering."""
        return await self.event_repo.get_by_run_id(run_id, after_id=after_id, limit=limit)

    async def get_themes(self, run_id: str) -> List[ThemeModel]:
        """Fetch thematic clusters extracted for a research run."""
        return await self.theme_repo.get_by_run_id(run_id)

    async def get_result(self, run_id: str) -> Optional[dict[str, Any]]:
        """Fetch completed literature review synthesis and final report."""
        run = await self.get_research_run(run_id)
        if not run:
            return None
        return {
            "run_id": run.id,
            "research_question": run.research_question,
            "status": run.status,
            "coverage_score": run.coverage,
            "stop_reason": run.stopping_reason,
            "final_review": run.final_review,
            "synthesis": run.synthesis,
            "reflection": run.reflection,
            "metadata": run.metadata_json or {},
        }

    async def get_evaluation(self, run_id: str) -> Optional[dict[str, Any]]:
        """Fetch evaluation metrics and benchmark comparisons."""
        run = await self.get_research_run(run_id)
        if not run:
            return None
        eval_data = run.evaluation or {
            "coverage": run.coverage,
            "relevance": 0.0,
            "coherence": 0.0,
            "citation_distribution": {},
            "evaluation_type": "intrinsic",
            "topic_coverage": None,
            "paper_recall": None,
            "benchmark_comparison": None,
        }
        eval_data["run_id"] = run.id
        return eval_data

    async def cancel_run(self, run_id: str) -> bool:
        """Cancel an in-progress research loop execution."""
        return ResearchRunner.cancel_run(run_id)
