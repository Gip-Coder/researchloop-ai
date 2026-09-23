"""
Tests for RelevanceFilter.
"""

from __future__ import annotations

import pytest
from backend.agent.filtering.relevance import RelevanceFilter
from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_relevance_filter_keeps_relevant_papers(mock_llm: MockLLMProvider, sample_plan: SearchPlan):
    rfilter = RelevanceFilter(llm_provider=mock_llm, threshold=0.5)

    p_relevant = Paper(
        id="rel-1",
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        abstract="Combines pre-trained parametric models with non-parametric retrieval to ground facts.",
        year=2020,
        source="arxiv"
    )
    p_irrelevant = Paper(
        id="irrel-1",
        title="Quantum Biology and Photosynthetic Energy Transfer in Cryptophyte Algae",
        abstract="Coherent energy transfer in light harvesting proteins.",
        year=2022,
        source="crossref"
    )

    relevant, rejected = await rfilter.filter_papers([p_relevant, p_irrelevant], sample_plan)

    assert len(relevant) == 1
    assert relevant[0].id == "rel-1"
    assert relevant[0].is_relevant is True
    assert relevant[0].relevance_score >= 0.5
    assert len(relevant[0].relevance_reason) > 0

    assert len(rejected) == 1
    assert rejected[0].id == "irrel-1"
    assert rejected[0].is_relevant is False


@pytest.mark.asyncio
async def test_relevance_filter_date_boundary(mock_llm: MockLLMProvider, sample_plan: SearchPlan):
    rfilter = RelevanceFilter(llm_provider=mock_llm)
    # Plan has date_range: 2020 to 2026
    p_old = Paper(
        id="old-1",
        title="Early Work on IR in 1995",
        abstract="Information retrieval indexing.",
        year=1995,
        source="crossref"
    )

    relevant, rejected = await rfilter.filter_papers([p_old], sample_plan)
    assert len(relevant) == 0
    assert len(rejected) == 1
    assert "Published in 1995" in rejected[0].relevance_reason

