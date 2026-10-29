"""
ResearchRunner service for executing the autonomous agent engine in the background,
broadcasting live AgentEvents, and persisting comprehensive research results.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, Set

from backend.agent.core.config import get_settings
from backend.agent.evaluation.benchmark import (
    CuratedBenchmarkReview,
    compare_against_benchmark,
)
from backend.agent.evaluation.metrics import (
    compute_citation_distribution,
    compute_coherence,
    compute_coverage,
    compute_relevance,
)
from backend.agent.models.common import AgentEvent
from backend.agent.models.research import ResearchConfig, ResearchResult
from backend.agent.orchestration.engine import ResearchEngine
from backend.database.models import (
    AgentEventModel,
    ResearchIterationModel,
    ResearchRunModel,
)
from backend.database.session import get_session_factory
from backend.repositories.event_repository import EventRepository
from backend.repositories.iteration_repository import IterationRepository
from backend.repositories.paper_repository import PaperRepository
from backend.repositories.research_repository import ResearchRepository
from backend.repositories.theme_repository import ThemeRepository

logger = logging.getLogger(__name__)

# In-memory subscription queues for real-time SSE / event streaming per run_id
_subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
_running_tasks: Dict[str, asyncio.Task] = {}


def register_listener(run_id: str, queue: asyncio.Queue) -> None:
    _subscribers[run_id].add(queue)


def unregister_listener(run_id: str, queue: asyncio.Queue) -> None:
    if run_id in _subscribers and queue in _subscribers[run_id]:
        _subscribers[run_id].remove(queue)
        if not _subscribers[run_id]:
            _subscribers.pop(run_id, None)


def broadcast_event(run_id: str, event_data: dict[str, Any]) -> None:
    if run_id in _subscribers:
        for q in list(_subscribers[run_id]):
            try:
                q.put_nowait(event_data)
            except Exception as e:
                logger.debug(f"Failed to push event to queue: {e}")


def _load_curated_benchmark(question: str) -> Optional[CuratedBenchmarkReview]:
    """Attempt to load matching curated benchmark review if question matches RAG factuality."""
    fixtures_path = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "curated_review.json"
    if fixtures_path.exists():
        try:
            data = json.loads(fixtures_path.read_text(encoding="utf-8"))
            benchmark = CuratedBenchmarkReview.model_validate(data)
            # Check question overlap
            q_norm = question.lower()
            if "rag" in q_norm or "retrieval augmented" in q_norm or "factuality" in q_norm:
                return benchmark
        except Exception as e:
            logger.warning(f"Could not load curated benchmark: {e}")
    return None


class ResearchRunner:
    """Executes ResearchEngine asynchronously and handles persistence and event distribution."""

    @classmethod
    async def run_in_background(cls, run_id: str) -> None:
        """Entry point for background task."""
        runner = cls(run_id)
        task = asyncio.create_task(runner.execute())
        _running_tasks[run_id] = task

        def _cleanup(t: asyncio.Task) -> None:
            _running_tasks.pop(run_id, None)

        task.add_done_callback(_cleanup)

    @classmethod
    def cancel_run(cls, run_id: str) -> bool:
        task = _running_tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.session_factory = get_session_factory()
        self._db_lock = asyncio.Lock()

    async def execute(self) -> None:
        logger.info(f"Starting execution for research run {self.run_id}")
        session = self.session_factory()
        research_repo = ResearchRepository(session)

        run = await research_repo.get_by_id(self.run_id)
        if not run:
            logger.error(f"Run {self.run_id} not found")
            await session.close()
            return

        # Mark started
        await research_repo.update_status(
            self.run_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        await session.close()

        # Build engine config
        run_config = run.config or {}
        settings = get_settings()

        # If user explicitly set mock_mode or settings say mock, enable mock_mode
        is_mock = run_config.get("mock_mode", False) or settings.is_mock_mode

        async def _event_callback(agent_event: AgentEvent) -> None:
            # 1. Persist event in DB
            evt_dict = {
                "id": agent_event.id,
                "run_id": self.run_id,
                "event_type": agent_event.type,
                "iteration": agent_event.iteration,
                "message": agent_event.message,
                "timestamp": agent_event.timestamp.isoformat(),
                "payload": agent_event.metadata,
            }
            try:
                async with self._db_lock:
                    async with self.session_factory() as evt_session:
                        evt_repo = EventRepository(evt_session)
                        model = AgentEventModel(
                            id=agent_event.id,
                            run_id=self.run_id,
                            event_type=agent_event.type,
                            iteration=agent_event.iteration,
                            message=agent_event.message,
                            timestamp=agent_event.timestamp,
                            payload=agent_event.metadata,
                        )
                        await evt_repo.create(model)

                        # Update current iteration and coverage on the run if available (unless terminal)
                        if agent_event.type not in ("research.completed", "research.failed"):
                            run_repo_inner = ResearchRepository(evt_session)
                            cov_update = None
                            if "coverage_score" in agent_event.metadata:
                                try:
                                    cov_update = float(agent_event.metadata["coverage_score"])
                                except (ValueError, TypeError):
                                    pass
                            await run_repo_inner.update_status(
                                self.run_id,
                                status="running",
                                current_iteration=agent_event.iteration,
                                coverage=cov_update,
                            )
            except Exception as e:
                logger.warning(f"Error persisting AgentEvent: {e}")

            # 2. Broadcast to live subscribers
            broadcast_event(self.run_id, evt_dict)

        engine_config = ResearchConfig(
            max_iterations=run_config.get("max_iterations", 3),
            target_coverage=run_config.get("target_coverage", 0.85),
            min_new_relevant_papers=run_config.get("min_new_relevant_papers", 1),
            llm_provider="mock" if is_mock else run_config.get("llm_provider", settings.llm_provider),
            llm_model=run_config.get("llm_model", settings.llm_model),
            preferred_sources=run_config.get("preferred_sources", list(settings.preferred_sources)),
            mock_mode=is_mock,
            temperature=run_config.get("temperature", 0.2),
            min_publication_year=run_config.get("min_publication_year", settings.default_min_publication_year),
            min_citations=run_config.get("min_citations", settings.default_min_citations),
            allow_unknown_citations=run_config.get("allow_unknown_citations", settings.default_allow_unknown_citations),
            preferred_min_citations=run_config.get("preferred_min_citations", settings.default_preferred_min_citations),
            preferred_max_citations=run_config.get("preferred_max_citations", settings.default_preferred_max_citations),
            strict_citation_filtering=run_config.get("strict_citation_filtering", settings.default_strict_citation_filtering),
            min_synthesis_papers=run_config.get("min_synthesis_papers", settings.default_min_synthesis_papers),
            target_synthesis_papers=run_config.get("target_synthesis_papers", settings.default_target_synthesis_papers),
            max_synthesis_papers=run_config.get("max_synthesis_papers", settings.default_max_synthesis_papers),
            allow_foundational_exceptions=run_config.get("allow_foundational_exceptions", settings.default_allow_foundational_exceptions),
            event_callback=_event_callback,
        )

        try:
            engine = ResearchEngine()
            result: ResearchResult = await engine.run(
                research_question=run.research_question,
                config=engine_config,
            )

            # Persist comprehensive result
            await self._persist_result(result)

            # Broadcast final completion or failure event to listeners
            final_evt_type = "research.completed" if result.status == "completed" else "research.failed"
            broadcast_event(
                self.run_id,
                {
                    "event_type": final_evt_type,
                    "status": result.status,
                    "coverage_score": result.coverage_score,
                    "stop_reason": result.stop_reason,
                    "error": result.stop_reason if result.status == "failed" else None,
                },
            )
            logger.info(f"Research run {self.run_id} finished with status={result.status}")

        except asyncio.CancelledError:
            logger.info(f"Research run {self.run_id} was cancelled")
            async with self.session_factory() as cancel_session:
                repo = ResearchRepository(cancel_session)
                await repo.update_status(self.run_id, status="cancelled", stopping_reason="User cancelled")
            broadcast_event(self.run_id, {"event_type": "research.cancelled", "status": "cancelled"})

        except Exception as e:
            logger.exception(f"Research run {self.run_id} failed: {e}")
            safe_error = str(e)
            async with self.session_factory() as err_session:
                repo = ResearchRepository(err_session)
                await repo.update_status(
                    self.run_id,
                    status="failed",
                    error=safe_error,
                    stopping_reason=f"error: {safe_error}",
                )
            broadcast_event(
                self.run_id,
                {
                    "event_type": "research.failed",
                    "status": "failed",
                    "error": safe_error,
                },
            )

    async def _persist_result(self, result: ResearchResult) -> None:
        """Persist papers, relations, themes, iterations, and final evaluations in a clean transaction."""
        async with self._db_lock:
            async with self.session_factory() as session:
                paper_repo = PaperRepository(session)
                iteration_repo = IterationRepository(session)
                theme_repo = ThemeRepository(session)
                research_repo = ResearchRepository(session)

                # 1. Upsert all papers discovered
                for paper in result.papers:
                    p_dict = paper.model_dump()
                    await paper_repo.upsert_paper(p_dict)
                    # Link to run
                    await paper_repo.link_run_paper(
                        run_id=self.run_id,
                        paper_id=paper.id,
                        iteration_number=1,  # Default
                        is_relevant=paper.is_relevant,
                        relevance_score=paper.relevance_score,
                        relevance_reason=paper.relevance_reason,
                    )

                # 2. Persist iterations
                for it in result.iterations:
                    it_model = ResearchIterationModel(
                        run_id=self.run_id,
                        iteration_number=it.iteration,
                        search_plan=it.search_plan.model_dump() if it.search_plan else None,
                        queries=it.queries_executed,
                        retrieved_count=it.papers_retrieved_count,
                        new_papers_count=it.new_papers_count,
                        relevant_count=it.relevant_papers_count,
                        coverage=it.coverage_score,
                        reflection=it.reflection.model_dump() if it.reflection else None,
                        created_at=it.timestamp,
                    )
                    session.add(it_model)
                await session.flush()

                # 3. Persist themes
                for theme in result.themes:
                    await theme_repo.save_theme(
                        run_id=self.run_id,
                        theme_id=theme.id,
                        title=theme.title,
                        description=theme.description,
                        paper_ids=theme.paper_ids,
                        key_findings=theme.key_findings,
                        contradictions_or_tensions=theme.contradictions_or_tensions,
                    )

                # 4. Compute evaluations
                coherence = compute_coherence(result.synthesis)
                avg_relevance = compute_relevance(result.relevant_papers)
                citation_stats = compute_citation_distribution(result.relevant_papers)
                coverage = result.coverage_score

                eval_dict: dict[str, Any] = {
                    "coverage": coverage,
                    "relevance": avg_relevance,
                    "coherence": coherence,
                    "citation_distribution": citation_stats,
                    "evaluation_type": "intrinsic",
                    "topic_coverage": None,
                    "paper_recall": None,
                    "benchmark_comparison": None,
                }

                benchmark = _load_curated_benchmark(result.research_question)
                if benchmark:
                    comparison = compare_against_benchmark(result, benchmark)
                    eval_dict["evaluation_type"] = "benchmark"
                    eval_dict["topic_coverage"] = comparison.topic_overlap_score
                    eval_dict["paper_recall"] = comparison.paper_recall
                    eval_dict["benchmark_comparison"] = comparison.model_dump()

                # 5. Save final result on research run record (single atomic commit at the end)
                err_msg = None
                if result.status == "failed" and result.stop_reason:
                    err_msg = result.stop_reason.removeprefix("error: ")
                await research_repo.save_final_result(
                    run_id=self.run_id,
                    status=result.status,
                    final_review=result.final_review,
                    synthesis=result.synthesis.model_dump() if result.synthesis else None,
                    reflection=result.reflection.model_dump() if result.reflection else None,
                    evaluation=eval_dict,
                    metadata=result.metadata,
                    coverage=result.coverage_score,
                    stopping_reason=result.stop_reason,
                    error=err_msg,
                )
