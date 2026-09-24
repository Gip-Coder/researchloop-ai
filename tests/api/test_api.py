"""
API endpoint tests for researchloop-ai.
"""

from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio
import httpx
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.api.main import create_app
from backend.database.models import Base, ResearchRunModel
from backend.database.session import get_db
import backend.database.session as session_module
from backend.services.research_runner import _running_tasks


@pytest_asyncio.fixture
async def test_client():
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

    # Cancel any running background tasks
    for task in list(_running_tasks.values()):
        if not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    session_module._session_factory = orig_factory
    session_module._engine = orig_engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_health_endpoint(test_client):
    client, _ = test_client
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "researchloop-ai"


@pytest.mark.asyncio
async def test_validation_errors_create_research(test_client):
    client, _ = test_client
    # Empty question
    res = await client.post("/api/research", json={"research_question": ""})
    assert res.status_code == 422

    # Too short
    res = await client.post("/api/research", json={"research_question": "Why?"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_and_get_research(test_client):
    client, _ = test_client
    payload = {
        "research_question": "What are current methods for factuality evaluation in RAG?",
        "config": {
            "max_iterations": 2,
            "target_coverage": 0.8,
            "mock_mode": True,
        },
    }
    response = await client.post("/api/research", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["status"] in ("pending", "running", "completed")
    run_id = data["id"]

    # Get by ID
    get_res = await client.get(f"/api/research/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == run_id

    # List
    list_res = await client.get("/api/research")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_unknown_run_returns_404(test_client):
    client, _ = test_client
    bad_id = "non-existent-id"
    for endpoint in [
        f"/api/research/{bad_id}",
        f"/api/research/{bad_id}/iterations",
        f"/api/research/{bad_id}/papers",
        f"/api/research/{bad_id}/themes",
        f"/api/research/{bad_id}/events",
        f"/api/research/{bad_id}/result",
        f"/api/research/{bad_id}/evaluation",
        f"/api/research/{bad_id}/cancel",
    ]:
        res = await (client.post(endpoint) if "cancel" in endpoint else client.get(endpoint))
        assert res.status_code == 404
