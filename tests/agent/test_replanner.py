"""
Tests for ReplanningAgent.
"""

from __future__ import annotations

import pytest
from backend.agent.replanning.replanner import ReplanningAgent
from backend.agent.models.research import ResearchState, ResearchIteration
from backend.agent.models.search import SearchPlan
from backend.agent.models.reflection import Reflection
from backend.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_replanner_generates_new_queries_targeting_gaps(mock_llm: MockLLMProvider, sample_plan: SearchPlan):
    replanner = ReplanningAgent(llm_provider=mock_llm)

    reflection = Reflection(
        coverage_score=0.60,
        relevance_score=0.85,
        missing_topics=["Evaluation benchmarks", "Hallucination metrics"],
        weak_areas=["Dense vs hybrid retrieval"],
        contradictions=[],
        outdated_areas=[],
        recommended_queries=[
            "RAG hallucination evaluation benchmarks",
            "retrieval augmented generation factuality metrics"
        ],
        should_replan=True,
        reason="Evaluation benchmarks missing.",
        evaluation_type="llm_critic"
    )

    state = ResearchState(
        research_question=sample_plan.research_question,
        iteration=1,
        search_plan=sample_plan,
        reflection=reflection,
        iteration_history=[
            ResearchIteration(
                iteration=1,
                search_plan=sample_plan,
                queries_executed=sample_plan.search_queries,
                papers_retrieved_count=20,
                new_papers_count=20,
                relevant_papers_count=10,
                coverage_score=0.60,
                reflection=reflection
            )
        ]
    )

    new_plan = await replanner.replan(state)

    assert isinstance(new_plan, SearchPlan)
    assert len(new_plan.search_queries) > 0

    # Ensure none of the newly produced queries duplicate previously executed queries
    prior_queries_lower = {q.lower().strip() for q in sample_plan.search_queries}
    for q in new_plan.search_queries:
        assert q.lower().strip() not in prior_queries_lower
