"""
Tests for CriticAgent.
"""

from __future__ import annotations

import pytest
from backend.agent.reflection.critic import CriticAgent
from backend.agent.models.research import ResearchState
from backend.agent.models.search import SearchPlan
from backend.agent.models.paper import Paper
from backend.agent.models.reflection import Reflection
from backend.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_critic_evaluation_iteration_1(mock_llm: MockLLMProvider, sample_plan: SearchPlan):
    critic = CriticAgent(llm_provider=mock_llm)

    state = ResearchState(
        research_question="How does retrieval augmented generation improve factuality in large language models?",
        iteration=1,
        search_plan=sample_plan,
        papers=[],
        relevant_papers=[
            Paper(id="p1", title="RAG Lewis 2020", source="arxiv", is_relevant=True)
        ]
    )

    reflection = await critic.evaluate(state)

    assert isinstance(reflection, Reflection)
    assert 0.0 <= reflection.coverage_score <= 1.0
    assert 0.0 <= reflection.relevance_score <= 1.0
    assert reflection.should_replan is True
    assert len(reflection.missing_topics) > 0
    assert len(reflection.recommended_queries) > 0
    assert len(reflection.reason) > 0
    assert reflection.evaluation_type == "llm_critic"


@pytest.mark.asyncio
async def test_critic_evaluation_iteration_2_satisfied(mock_llm: MockLLMProvider, sample_plan: SearchPlan):
    critic = CriticAgent(llm_provider=mock_llm)

    state = ResearchState(
        research_question="How does retrieval augmented generation improve factuality in large language models?",
        iteration=2,
        search_plan=sample_plan,
        papers=[],
        relevant_papers=[
            Paper(id="p1", title="RAG Lewis 2020", source="arxiv", is_relevant=True),
            Paper(id="p2", title="RGB Benchmark 2024", source="arxiv", is_relevant=True),
            Paper(id="p3", title="FactScore 2023", source="crossref", is_relevant=True)
        ]
    )

    reflection = await critic.evaluate(state)

    assert isinstance(reflection, Reflection)
    assert reflection.coverage_score >= 0.85
    assert reflection.should_replan is False

