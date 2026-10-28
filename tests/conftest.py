"""
Pytest configuration and shared test fixtures for researchloop-ai.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import pytest
import pytest_asyncio
import httpx
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.agent.evaluation.benchmark import CuratedBenchmarkReview
from backend.providers.llm.mock import MockLLMProvider
from backend.agent.retrieval.mock_retriever import MockAcademicProvider
from backend.api.main import create_app
from backend.database.models import Base
from backend.database.session import get_db
import backend.database.session as session_module
from backend.services.research_runner import _running_tasks

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_papers() -> list[Paper]:
    raw = json.loads((FIXTURES_DIR / "sample_papers.json").read_text(encoding="utf-8"))
    return [Paper.model_validate(p) for p in raw]


@pytest.fixture
def sample_plan() -> SearchPlan:
    raw = json.loads((FIXTURES_DIR / "sample_plans.json").read_text(encoding="utf-8"))
    return SearchPlan.model_validate(raw)


@pytest.fixture
def sample_curated_benchmark() -> CuratedBenchmarkReview:
    raw = json.loads((FIXTURES_DIR / "curated_review.json").read_text(encoding="utf-8"))
    return CuratedBenchmarkReview.model_validate(raw)


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    return MockLLMProvider()


@pytest.fixture
def mock_academic() -> MockAcademicProvider:
    return MockAcademicProvider()


@pytest.fixture(autouse=True)
def isolate_test_cache(tmp_path, monkeypatch):
    """Ensure test runs use a clean isolated cache directory and cannot be poisoned by disk artifacts."""
    import backend.agent.core.config as config_mod
    test_cache_dir = str(tmp_path / "test_cache")
    monkeypatch.setenv("CACHE_DIR", test_cache_dir)
    if config_mod._SETTINGS_INSTANCE is not None:
        config_mod._SETTINGS_INSTANCE.cache_dir = test_cache_dir


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
