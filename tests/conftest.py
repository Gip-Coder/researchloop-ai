"""
Pytest configuration and shared test fixtures for researchloop-ai.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.agent.evaluation.benchmark import CuratedBenchmarkReview
from backend.providers.llm.mock import MockLLMProvider
from backend.agent.retrieval.mock_retriever import MockAcademicProvider

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

