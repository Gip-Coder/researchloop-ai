"""
Mocked unit tests for academic providers (100% offline).
"""

from __future__ import annotations

import httpx
import pytest
from unittest.mock import AsyncMock, patch

from backend.agent.retrieval.mock_retriever import MockAcademicProvider
from backend.agent.retrieval.semantic_scholar import SemanticScholarProvider
from backend.agent.retrieval.arxiv import ArxivProvider
from backend.agent.retrieval.crossref import CrossrefProvider
from backend.agent.retrieval.multi_retriever import MultiProviderRetriever
from backend.agent.models.search import SearchPlan
from backend.agent.models.common import AgentEvent


@pytest.mark.asyncio
async def test_mock_academic_provider_search():
    provider = MockAcademicProvider()
    results = await provider.search("retrieval augmented generation factuality", limit=5)
    assert len(results) > 0
    assert any("Retrieval-Augmented" in p.title for p in results)


@pytest.mark.asyncio
async def test_mock_academic_provider_year_filter():
    provider = MockAcademicProvider()
    results = await provider.search("RAG", start_year=2024, end_year=2026)
    assert len(results) > 0
    for p in results:
        if p.year:
            assert 2024 <= p.year <= 2026


@pytest.mark.asyncio
async def test_semantic_scholar_normalization_mocked():
    provider = SemanticScholarProvider(api_key="test-key")
    mock_payload = {
        "data": [
            {
                "paperId": "s2-mock-id",
                "title": "Mock S2 Study on LLMs",
                "authors": [{"name": "Alice Smith"}, {"name": "Bob Jones"}],
                "abstract": "An empirical inquiry into transformer reasoning.",
                "year": 2023,
                "venue": "ACL 2023",
                "citationCount": 42,
                "externalIds": {"DOI": "10.18653/v1/mock", "ArXiv": "2301.00001"},
                "url": "https://www.semanticscholar.org/paper/s2-mock-id"
            }
        ]
    }

    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "https://api.semanticscholar.org"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        papers = await provider.search("mock query")
        assert len(papers) == 1
        p = papers[0]
        assert p.title == "Mock S2 Study on LLMs"
        assert p.doi == "10.18653/v1/mock"
        assert p.authors == ["Alice Smith", "Bob Jones"]
        assert p.citation_count == 42
        assert p.source == "semantic_scholar"


@pytest.mark.asyncio
async def test_arxiv_xml_normalization_mocked():
    provider = ArxivProvider()
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2301.12345v1</id>
        <title>Self-Reflective RAG for Factuality</title>
        <summary>A detailed abstract describing self-reflective mechanisms in language models.</summary>
        <author><name>Carol White</name></author>
        <published>2023-01-15T00:00:00Z</published>
        <arxiv:doi>10.48550/arXiv.2301.12345</arxiv:doi>
        <category term="cs.CL"/>
      </entry>
    </feed>"""

    mock_resp = httpx.Response(200, text=mock_xml, request=httpx.Request("GET", "http://export.arxiv.org"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        papers = await provider.search("self-reflective rag")
        assert len(papers) == 1
        p = papers[0]
        assert p.title == "Self-Reflective RAG for Factuality"
        assert p.year == 2023
        assert p.authors == ["Carol White"]
        assert p.doi == "10.48550/arXiv.2301.12345"
        assert p.source == "arxiv"


@pytest.mark.asyncio
async def test_crossref_json_normalization_mocked():
    provider = CrossrefProvider()
    mock_payload = {
        "message": {
            "items": [
                {
                    "title": ["Empirical Evaluation of RAG Benchmarks"],
                    "author": [{"given": "Dave", "family": "Miller"}],
                    "abstract": "<jats:p>Abstract with JATS tags.</jats:p>",
                    "published": {"date-parts": [[2024, 3, 10]]},
                    "DOI": "10.1145/mock.doi",
                    "is-referenced-by-count": 15,
                    "container-title": ["ACM Transactions"]
                }
            ]
        }
    }

    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "https://api.crossref.org"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        papers = await provider.search("rag benchmarks")
        assert len(papers) == 1
        p = papers[0]
        assert p.title == "Empirical Evaluation of RAG Benchmarks"
        assert p.year == 2024
        assert p.authors == ["Dave Miller"]
        assert p.abstract == "Abstract with JATS tags."
        assert p.doi == "10.1145/mock.doi"
        assert p.citation_count == 15
        assert p.source == "crossref"


@pytest.mark.asyncio
async def test_multi_provider_retriever_failure_isolation():
    """Verify that if one provider fails, the retriever isolates the failure and collects other results."""
    good_provider = MockAcademicProvider(name="good_source")

    class CrashingProvider(MockAcademicProvider):
        def __init__(self):
            super().__init__(name="failing_source")

        async def search(self, *args, **kwargs):
            raise httpx.ConnectTimeout("Semantic Scholar gateway timed out")

    events: list[AgentEvent] = []

    async def _on_event(evt: AgentEvent):
        events.append(evt)

    multi = MultiProviderRetriever(
        providers=[good_provider, CrashingProvider()],
        cache_enabled=False
    )

    plan = SearchPlan(
        research_question="Test RAG",
        search_queries=["query 1"],
        preferred_sources=["good_source", "failing_source"]
    )

    papers = await multi.retrieve_for_plan(plan, iteration=1, event_callback=_on_event)

    # Good provider succeeded
    assert len(papers) > 0

    # Failure was captured and emitted
    failed_events = [e for e in events if e.type == "retrieval.failed"]
    assert len(failed_events) == 1
    assert "failing_source" in failed_events[0].message

