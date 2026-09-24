"""
Tests for SQLAlchemy database models and persistence layer.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.models import (
    Base,
    ResearchRunModel,
    ResearchIterationModel,
    PaperModel,
    ResearchRunPaperModel,
    ThemeModel,
    AgentEventModel,
)
from backend.repositories.research_repository import ResearchRepository
from backend.repositories.iteration_repository import IterationRepository
from backend.repositories.paper_repository import PaperRepository
from backend.repositories.theme_repository import ThemeRepository
from backend.repositories.event_repository import EventRepository


@pytest_asyncio.fixture
async def test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_query_research_run(test_session: AsyncSession):
    repo = ResearchRepository(test_session)
    run = ResearchRunModel(
        research_question="How does retrieval augmented generation improve factuality?",
        status="pending",
        max_iterations=3,
    )
    created = await repo.create(run)
    assert created.id is not None
    assert created.status == "pending"
    assert created.research_question == "How does retrieval augmented generation improve factuality?"

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.current_iteration == 0


@pytest.mark.asyncio
async def test_update_status_and_final_result(test_session: AsyncSession):
    repo = ResearchRepository(test_session)
    run = ResearchRunModel(
        research_question="Sample question",
        status="pending",
    )
    created = await repo.create(run)

    updated = await repo.update_status(created.id, status="running", current_iteration=1, coverage=0.65)
    assert updated.status == "running"
    assert updated.current_iteration == 1
    assert updated.coverage == 0.65

    final = await repo.save_final_result(
        run_id=created.id,
        status="completed",
        final_review={"title": "Review", "narrative": "Done"},
        synthesis={"summary": "Synthetic"},
        reflection={"score": 0.9},
        evaluation={"coherence": 1.0},
        metadata={"total_papers": 5},
        coverage=0.90,
        stopping_reason="target_coverage_reached",
    )
    assert final.status == "completed"
    assert final.coverage == 0.90
    assert final.stopping_reason == "target_coverage_reached"
    assert final.final_review["title"] == "Review"


@pytest.mark.asyncio
async def test_paper_repository_upsert_and_link(test_session: AsyncSession):
    run_repo = ResearchRepository(test_session)
    paper_repo = PaperRepository(test_session)

    run = await run_repo.create(ResearchRunModel(research_question="Question"))

    paper_data = {
        "id": "paper-123",
        "title": "Retrieval-Augmented Generation for NLP Tasks",
        "authors": ["Author One", "Author Two"],
        "abstract": "Grounding generation in retrieval.",
        "year": 2020,
        "venue": "NeurIPS",
        "doi": "10.1234/5678",
        "url": "https://arxiv.org/abs/2005.11401",
        "source": "arxiv",
        "citation_count": 500,
    }

    paper = await paper_repo.upsert_paper(paper_data)
    assert paper.id == "paper-123"

    link = await paper_repo.link_run_paper(
        run_id=run.id,
        paper_id=paper.id,
        iteration_number=1,
        is_relevant=True,
        relevance_score=0.92,
        relevance_reason="Foundational paper",
    )
    assert link.is_relevant is True
    assert link.relevance_score == 0.92

    # Query with filters
    results = await paper_repo.get_papers_for_run(run.id, is_relevant=True, search="Retrieval")
    assert len(results) == 1
    p, l = results[0]
    assert p.id == "paper-123"
    assert l.relevance_score == 0.92


@pytest.mark.asyncio
async def test_iteration_and_events_persistence(test_session: AsyncSession):
    run_repo = ResearchRepository(test_session)
    it_repo = IterationRepository(test_session)
    event_repo = EventRepository(test_session)
    theme_repo = ThemeRepository(test_session)

    run = await run_repo.create(ResearchRunModel(research_question="Event trace question"))

    # Iteration
    it = ResearchIterationModel(
        run_id=run.id,
        iteration_number=1,
        search_plan={"queries": ["query1"]},
        queries=["query1"],
        retrieved_count=20,
        new_papers_count=10,
        relevant_count=5,
        coverage=0.6,
    )
    await it_repo.create(it)

    # Event
    evt = AgentEventModel(
        run_id=run.id,
        event_type="planner.completed",
        iteration=1,
        message="Search plan formulated.",
        payload={"query_count": 3},
    )
    await event_repo.create(evt)

    # Theme
    await theme_repo.save_theme(
        run_id=run.id,
        theme_id="theme-1",
        title="Grounding Generative Models",
        description="Non-parametric grounding mechanisms.",
        paper_ids=["paper-1"],
        key_findings=["Reduces errors"],
        contradictions_or_tensions=[],
    )

    # Verify query
    its = await it_repo.get_by_run_id(run.id)
    assert len(its) == 1
    assert its[0].relevant_count == 5

    events = await event_repo.get_by_run_id(run.id)
    assert len(events) == 1
    assert events[0].event_type == "planner.completed"

    themes = await theme_repo.get_by_run_id(run.id)
    assert len(themes) == 1
    assert themes[0].title == "Grounding Generative Models"
