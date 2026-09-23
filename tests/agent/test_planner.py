"""
Tests for PlanningAgent.
"""

from __future__ import annotations

import pytest
from backend.agent.planner.planner import PlanningAgent
from backend.agent.models.search import SearchPlan
from backend.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_planner_normal_question(mock_llm: MockLLMProvider):
    planner = PlanningAgent(llm_provider=mock_llm)
    question = "How does retrieval augmented generation improve factuality in large language models?"

    plan = await planner.plan(question)

    assert isinstance(plan, SearchPlan)
    assert plan.research_question == question
    assert len(plan.sub_questions) >= 3
    assert len(plan.keywords) >= 4
    assert len(plan.search_queries) >= 3
    assert "arxiv" in plan.preferred_sources
    assert len(plan.inclusion_criteria) > 0
    assert len(plan.exclusion_criteria) > 0


@pytest.mark.asyncio
async def test_planner_complex_interdisciplinary_question(mock_llm: MockLLMProvider):
    planner = PlanningAgent(llm_provider=mock_llm)
    question = "What are the computational trade-offs of neuro-symbolic reasoning vs transformers in clinical decision support?"

    plan = await planner.plan(question)

    assert isinstance(plan, SearchPlan)
    assert len(plan.search_queries) > 0
    assert len(plan.sub_questions) > 0


@pytest.mark.asyncio
async def test_planner_fallback_on_llm_failure():
    class BrokenLLM(MockLLMProvider):
        async def generate_structured(self, *args, **kwargs):
            raise RuntimeError("Simulated total LLM failure")

    planner = PlanningAgent(llm_provider=BrokenLLM())
    question = "How does speculative decoding accelerate autoregressive generation?"

    plan = await planner.plan(question)

    assert isinstance(plan, SearchPlan)
    assert plan.research_question == question
    assert len(plan.search_queries) > 0
    assert len(plan.sub_questions) > 0
