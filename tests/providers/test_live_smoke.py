"""
Optional live smoke tests against real external APIs.
SKIPPED BY DEFAULT in all automated test runs.
To execute live smoke tests, set RUN_LIVE_API_TESTS=1 in your environment.
"""

from __future__ import annotations

import os
import pytest

from backend.agent.retrieval.arxiv import ArxivProvider
from backend.agent.retrieval.crossref import CrossrefProvider

LIVE_TESTS_ENABLED = os.getenv("RUN_LIVE_API_TESTS", "0") == "1"


@pytest.mark.smoke
@pytest.mark.skipif(not LIVE_TESTS_ENABLED, reason="Live API tests disabled. Set RUN_LIVE_API_TESTS=1 to run.")
@pytest.mark.asyncio
async def test_live_arxiv_smoke():
    provider = ArxivProvider(timeout=10.0)
    results = await provider.search("retrieval augmented generation", limit=2)
    assert len(results) > 0
    assert results[0].source == "arxiv"
    assert results[0].title != ""


@pytest.mark.smoke
@pytest.mark.skipif(not LIVE_TESTS_ENABLED, reason="Live API tests disabled. Set RUN_LIVE_API_TESTS=1 to run.")
@pytest.mark.asyncio
async def test_live_crossref_smoke():
    provider = CrossrefProvider(timeout=10.0)
    results = await provider.search("large language models", limit=2)
    assert len(results) > 0
    assert results[0].source == "crossref"
    assert results[0].title != ""
