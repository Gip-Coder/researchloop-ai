"""
Tests for SynthesisAgent.
"""

from __future__ import annotations

import pytest
from backend.agent.synthesis.synthesizer import SynthesisAgent
from backend.agent.models.paper import Paper
from backend.agent.models.synthesis import Synthesis
from backend.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_synthesis_empty_paper_list(mock_llm: MockLLMProvider):
    synthesizer = SynthesisAgent(llm_provider=mock_llm)
    result = await synthesizer.synthesize("What is RAG?", [])

    assert isinstance(result, Synthesis)
    assert len(result.paper_analyses) == 0
    assert len(result.themes) == 0


@pytest.mark.asyncio
async def test_synthesis_with_papers(mock_llm: MockLLMProvider, sample_papers: list[Paper]):
    synthesizer = SynthesisAgent(llm_provider=mock_llm)
    relevant = [p for p in sample_papers if "Agricultural" not in p.title]

    result = await synthesizer.synthesize(
        "How does retrieval augmented generation improve factuality in large language models?",
        relevant
    )

    assert isinstance(result, Synthesis)
    assert len(result.paper_analyses) > 0
    assert len(result.themes) > 0
    assert len(result.agreements) > 0
    assert len(result.differences) > 0
    assert len(result.research_gaps) > 0
    assert len(result.narrative_summary) > 50

    # Verify per-paper extraction fields
    first_analysis = result.paper_analyses[0]
    assert first_analysis.research_problem != ""
    assert first_analysis.methodology != ""
    assert first_analysis.contribution != ""
    assert len(first_analysis.key_findings) > 0

