"""
Acceptance test suite for Phase 3:
- PREFERRED_SOURCES parsing (whitespace, case normalization, deduplication, unknown names)
- Default configuration excludes Semantic Scholar
- Semantic Scholar is NOT initialized or queried by default
- Explicit configuration of Semantic Scholar enables it
"""

import pytest
from backend.agent.core.config import parse_preferred_sources, get_settings
from backend.agent.retrieval.multi_retriever import MultiProviderRetriever
from backend.agent.retrieval.arxiv import ArxivProvider
from backend.agent.retrieval.crossref import CrossrefProvider
from backend.agent.retrieval.semantic_scholar import SemanticScholarProvider
from backend.agent.models.search import SearchPlan


def test_parse_preferred_sources():
    """Verify parsing handles commas, whitespace, casing, invalid sources, and duplicates."""
    # Defaults
    assert parse_preferred_sources("") == ["arxiv", "crossref"]
    assert parse_preferred_sources(None) == ["arxiv", "crossref"]

    # Valid string
    assert parse_preferred_sources("arxiv,crossref") == ["arxiv", "crossref"]

    # Whitespace and casing
    assert parse_preferred_sources("  ARXIV ,  Crossref  ") == ["arxiv", "crossref"]

    # Deduplication preserving order
    assert parse_preferred_sources("arxiv,crossref,arxiv,CROSSREF") == ["arxiv", "crossref"]

    # Unknown source filtered out with fallback
    assert parse_preferred_sources("google_scholar,bing_academic") == ["arxiv", "crossref"]
    assert parse_preferred_sources("arxiv,unknown_source,crossref") == ["arxiv", "crossref"]

    # Explicitly enabling semantic scholar
    assert parse_preferred_sources("arxiv,crossref,semantic_scholar") == ["arxiv", "crossref", "semantic_scholar"]


def test_default_multi_retriever_does_not_initialize_semantic_scholar():
    """Verify MultiProviderRetriever excludes Semantic Scholar by default."""
    retriever = MultiProviderRetriever(mock_mode=False)

    # By default, semantic_scholar must NOT be instantiated
    assert "arxiv" in retriever.providers
    assert "crossref" in retriever.providers
    assert "semantic_scholar" not in retriever.providers

    # Verify provider types
    assert isinstance(retriever.providers["arxiv"], ArxivProvider)
    assert isinstance(retriever.providers["crossref"], CrossrefProvider)


def test_explicit_semantic_scholar_initialization():
    """When PREFERRED_SOURCES includes semantic_scholar, it is registered."""
    import os
    from unittest.mock import patch

    with patch.dict(os.environ, {"PREFERRED_SOURCES": "arxiv,crossref,semantic_scholar"}):
        settings = get_settings(reload=True)
        assert "semantic_scholar" in settings.preferred_sources

        retriever = MultiProviderRetriever(mock_mode=False)
        assert "semantic_scholar" in retriever.providers
        assert isinstance(retriever.providers["semantic_scholar"], SemanticScholarProvider)

    # Reset back to default
    get_settings(reload=True)


@pytest.mark.asyncio
async def test_excluded_providers_never_queried():
    """Even if a search plan lists an excluded provider, it is never called."""
    retriever = MultiProviderRetriever(mock_mode=True)
    assert "semantic_scholar" not in retriever.providers

    # Search plan requesting semantic_scholar
    plan = SearchPlan(
        research_question="Test query isolation",
        search_queries=['"query test"'],
        preferred_sources=["semantic_scholar", "arxiv"]
    )

    papers = await retriever.retrieve_for_plan(plan)
    # Only arxiv papers returned; semantic_scholar never queried
    sources = {p.source for p in papers}
    assert "semantic_scholar" not in sources
