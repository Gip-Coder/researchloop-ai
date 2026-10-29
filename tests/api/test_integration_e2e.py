"""
End-to-End Integration Test for researchloop-ai.
Executes the full pipeline:
HTTP POST -> Service -> Background Task -> Actual ResearchEngine (mock mode)
-> Real-time Event streaming -> Multi-table Persistence -> HTTP GET verification.

Zero external credentials required.
"""

from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio
import httpx
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.api.main import create_app
from backend.database.models import Base
from backend.database.session import get_db
import backend.database.session as session_module


@pytest_asyncio.fixture
async def e2e_client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    orig_factory = session_module._session_factory
    orig_engine = session_module._engine
    session_module._session_factory = session_factory
    session_module._engine = engine

    app = create_app()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    session_module._session_factory = orig_factory
    session_module._engine = orig_engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_full_end_to_end_research_lifecycle(e2e_client):
    """
    Verifies full lifecycle with Member 1's actual ResearchEngine in mock mode.
    Tests POST /api/research -> background execution -> polling -> complete data retrieval.
    """
    client, _ = e2e_client

    research_payload = {
        "research_question": "What are the current methods for factuality evaluation in retrieval-augmented generation?",
        "config": {
            "max_iterations": 3,
            "target_coverage": 0.85,
            "mock_mode": True,
            "llm_provider": "mock",
        },
    }

    # 1. Initiate research
    post_res = await client.post("/api/research", json=research_payload)
    assert post_res.status_code == 201
    run_data = post_res.json()
    run_id = run_data["id"]
    assert run_id is not None
    assert run_data["research_question"] == research_payload["research_question"]

    # 2. Wait for completion (with timeout)
    max_wait = 25.0
    elapsed = 0.0
    poll_interval = 0.2
    completed_run = None

    while elapsed < max_wait:
        get_res = await client.get(f"/api/research/{run_id}")
        assert get_res.status_code == 200
        current_data = get_res.json()
        if current_data["status"] in ("completed", "failed"):
            completed_run = current_data
            break
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    assert completed_run is not None, "Research run did not complete within timeout"
    assert completed_run["status"] == "completed", f"Run failed with: {completed_run.get('error')}"
    assert completed_run["coverage"] >= 0.85
    assert completed_run["stopping_reason"] in ("target_coverage_reached", "critic_satisfied_coverage")

    # 3. Verify Iterations endpoint
    it_res = await client.get(f"/api/research/{run_id}/iterations")
    assert it_res.status_code == 200
    iterations = it_res.json()
    assert len(iterations) >= 2, "Expected at least 2 iterations for RAG mock scenario"
    # Iteration 1 had gaps; Iteration 2 addressed them
    assert iterations[0]["iteration_number"] == 1
    assert iterations[1]["iteration_number"] == 2
    assert iterations[0]["coverage"] <= iterations[1]["coverage"]

    # 4. Verify Papers endpoint with filters
    papers_res = await client.get(f"/api/research/{run_id}/papers")
    assert papers_res.status_code == 200
    papers = papers_res.json()
    assert len(papers) >= 7

    # Filter relevant papers
    relevant_res = await client.get(f"/api/research/{run_id}/papers?is_relevant=true")
    assert relevant_res.status_code == 200
    rel_papers = relevant_res.json()
    assert len(rel_papers) >= 6
    for p in rel_papers:
        assert p["is_relevant"] is True
        assert p["relevance_score"] is not None
        assert p["title"] != ""

    # 5. Verify Themes endpoint
    themes_res = await client.get(f"/api/research/{run_id}/themes")
    assert themes_res.status_code == 200
    themes = themes_res.json()
    assert len(themes) >= 1
    assert all("not thematically interpreted" in t["title"].lower() for t in themes)

    # 6. Verify Events trace endpoint
    events_res = await client.get(f"/api/research/{run_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 10
    event_types = [e["event_type"] for e in events]
    assert "research.started" in event_types
    assert "planner.started" in event_types
    assert "retrieval.started" in event_types
    assert "synthesis.started" in event_types
    assert "reflection.completed" in event_types
    assert "research.completed" in event_types

    # 7. Verify Final Review / Result endpoint
    result_res = await client.get(f"/api/research/{run_id}/result")
    assert result_res.status_code == 200
    result = result_res.json()
    assert result["status"] == "completed"
    assert result["coverage_score"] >= 0.85
    final_review = result["final_review"]
    assert final_review is not None
    assert "narrative" in final_review
    assert len(final_review["narrative"]) > 50
    assert len(final_review["key_themes"]) == 1
    assert "not thematically interpreted" in final_review["key_themes"][0]["title"].lower()
    assert {row["paper_id"] for row in final_review["evidence_matrix"] if row["included_in_synthesis"]} == {
        paper["id"] for paper in final_review["bibliography"]
    }
    assert final_review["consensus_findings"] == []
    assert any("does not perform substantive" in warning for warning in final_review["quality_warnings"])

    # 8. Verify Evaluation endpoint
    eval_res = await client.get(f"/api/research/{run_id}/evaluation")
    assert eval_res.status_code == 200
    evaluation = eval_res.json()
    assert evaluation["coverage"] >= 0.85
    assert evaluation["coherence"] > 0.5
    assert evaluation["relevance"] > 0.8
    assert "total_citations" in evaluation["citation_distribution"]
    assert evaluation["evaluation_type"] == "benchmark"
    assert evaluation["benchmark_comparison"] is not None
    assert evaluation["benchmark_comparison"]["paper_recall"] > 0.0
