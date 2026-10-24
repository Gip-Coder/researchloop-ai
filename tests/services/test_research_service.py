"""
Tests for application service layer: ResearchService and ResearchRunner.
"""

from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.api.schemas.research import ResearchConfigInput
from backend.database.models import Base
import backend.database.session as session_module
from backend.services.research_service import ResearchService
from backend.services.research_runner import ResearchRunner


@pytest_asyncio.fixture
async def app_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # Monkeypatch session factory
    orig_factory = session_module._session_factory
    orig_engine = session_module._engine
    session_module._session_factory = factory
    session_module._engine = engine

    yield factory

    session_module._session_factory = orig_factory
    session_module._engine = orig_engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_query_service(app_db):
    async with app_db() as session:
        service = ResearchService(session)
        config = ResearchConfigInput(max_iterations=2, target_coverage=0.80, mock_mode=True)
        run = await service.create_research_run(
            research_question="What are current methods for factuality evaluation in RAG?",
            config=config,
        )

        assert run.id is not None
        assert run.status == "pending"
        assert run.max_iterations == 2

        fetched = await service.get_research_run(run.id)
        assert fetched is not None
        assert fetched.id == run.id

        runs = await service.list_runs()
        assert len(runs) >= 1


@pytest.mark.asyncio
async def test_research_runner_mock_execution(app_db):
    """
    Execute ResearchRunner end-to-end with Member 1's mock mode agent engine.
    Verifies that the runner executes, emits events, persists iterations, papers, themes,
    and updates status to completed.
    """
    run_id = None
    async with app_db() as session:
        service = ResearchService(session)
        config = ResearchConfigInput(max_iterations=3, target_coverage=0.85, mock_mode=True)
        run = await service.create_research_run(
            research_question="What are current methods for factuality evaluation in RAG?",
            config=config,
        )
        run_id = run.id

    # Execute runner directly
    runner = ResearchRunner(run_id)
    await runner.execute()

    # Verify persistence
    async with app_db() as session:
        service = ResearchService(session)
        completed_run = await service.get_research_run(run_id)
        assert completed_run.status == "completed"
        assert completed_run.coverage >= 0.85
        assert completed_run.stopping_reason in ("target_coverage_reached", "critic_satisfied_coverage")
        assert completed_run.completed_at is not None

        # Verify iterations
        iterations = await service.get_iterations(run_id)
        assert len(iterations) >= 1
        assert iterations[0].iteration_number == 1
        assert iterations[0].retrieved_count > 0

        # Verify papers
        papers = await service.get_papers(run_id)
        assert len(papers) > 0
        paper, link = papers[0]
        assert paper.title is not None
        assert link.is_relevant is not None

        # Verify events
        events = await service.get_events(run_id)
        assert len(events) >= 5
        event_types = [e.event_type for e in events]
        assert "research.started" in event_types
        assert "research.completed" in event_types

        # Verify themes
        themes = await service.get_themes(run_id)
        assert len(themes) >= 1

        # Verify result & evaluation
        result = await service.get_result(run_id)
        assert result is not None
        assert "final_review" in result
        assert result["final_review"]["title"] != ""

        evaluation = await service.get_evaluation(run_id)
        assert evaluation is not None
        assert evaluation["coherence"] > 0.0
        assert evaluation["relevance"] > 0.0


@pytest.mark.asyncio
async def test_research_runner_handles_engine_failure(app_db, monkeypatch):
    """Regression test: if ResearchEngine returns status='failed', ResearchRunner records error and broadcasts research.failed."""
    from backend.agent.models.research import ResearchResult
    from backend.agent.orchestration.engine import ResearchEngine
    from backend.services.research_runner import register_listener, unregister_listener

    async def _mock_failed_run(self, research_question, config=None):
        return ResearchResult(
            session_id="err-session",
            status="failed",
            research_question=research_question,
            stop_reason="error: Simulated unrecoverable failure",
            coverage_score=0.0,
        )

    monkeypatch.setattr(ResearchEngine, "run", _mock_failed_run)

    async with app_db() as session:
        service = ResearchService(session)
        run = await service.create_research_run(
            research_question="How does failure recovery work?",
            config=ResearchConfigInput(mock_mode=True),
        )
        run_id = run.id

    queue: asyncio.Queue = asyncio.Queue()
    register_listener(run_id, queue)
    try:
        runner = ResearchRunner(run_id)
        await runner.execute()

        evt = queue.get_nowait()
        assert evt["event_type"] == "research.failed"
        assert evt["status"] == "failed"
    finally:
        unregister_listener(run_id, queue)

    async with app_db() as session:
        service = ResearchService(session)
        failed_run = await service.get_research_run(run_id)
        assert failed_run.status == "failed"
        assert "Simulated unrecoverable failure" in (failed_run.error or "")
