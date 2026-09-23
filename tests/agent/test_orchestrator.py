"""
Tests for ResearchEngine orchestrator.
"""

from __future__ import annotations

import pytest
from backend.agent.orchestration.engine import ResearchEngine
from backend.agent.models.research import ResearchConfig, ResearchResult
from backend.agent.models.common import AgentEvent, EventType


@pytest.mark.asyncio
async def test_orchestrator_multi_iteration_run():
    events_captured: list[AgentEvent] = []

    async def _on_event(evt: AgentEvent):
        events_captured.append(evt)

    config = ResearchConfig(
        max_iterations=2,
        target_coverage=0.85,
        mock_mode=True,
        event_callback=_on_event
    )
    engine = ResearchEngine(default_config=config)

    question = "How does retrieval augmented generation improve factuality in large language models?"
    result = await engine.run(question, config=config)

    assert isinstance(result, ResearchResult)
    assert result.status == "completed"
    assert result.research_question == question
    assert result.coverage_score >= 0.85
    assert result.stop_reason in ("target_coverage_reached", "critic_satisfied_coverage", "max_iterations_reached")
    assert len(result.iterations) >= 1
    assert len(result.papers) > 0
    assert len(result.relevant_papers) > 0
    assert len(result.themes) > 0
    assert result.synthesis is not None
    assert len(result.events) > 0

    # Verify event stream
    event_types = {e.type for e in events_captured}
    assert EventType.RESEARCH_STARTED.value in event_types
    assert EventType.PLANNER_STARTED.value in event_types
    assert EventType.RETRIEVAL_STARTED.value in event_types
    assert EventType.FILTER_COMPLETED.value in event_types
    assert EventType.SYNTHESIS_STARTED.value in event_types
    assert EventType.REFLECTION_STARTED.value in event_types
    assert EventType.RESEARCH_COMPLETED.value in event_types


@pytest.mark.asyncio
async def test_orchestrator_stops_at_max_iterations():
    config = ResearchConfig(
        max_iterations=1,
        target_coverage=0.99,  # High target so it stops solely due to max_iterations
        mock_mode=True
    )
    engine = ResearchEngine(default_config=config)

    result = await engine.run("What is knowledge grounding in RAG?", config=config)

    assert result.status == "completed"
    assert len(result.iterations) == 1
    assert result.stop_reason == "max_iterations_reached"


@pytest.mark.asyncio
async def test_orchestrator_diminishing_returns_stop():
    # If target coverage is high, but min_new_relevant_papers=999, it should stop on iteration 2
    config = ResearchConfig(
        max_iterations=4,
        target_coverage=0.99,
        min_new_relevant_papers=999,  # Impossible threshold
        mock_mode=True
    )
    engine = ResearchEngine(default_config=config)

    result = await engine.run("What is knowledge grounding in RAG?", config=config)

    assert result.status == "completed"
    assert result.stop_reason == "diminishing_returns_no_new_papers"

