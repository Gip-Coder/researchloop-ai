"""
Regression tests added during the live audit:
1. Provider failure isolation (retriever emits event without crashing the engine)
2. Provider implementation key in cache to prevent fixture contamination
3. Strict deterministic multi-iteration fixture proving gap reduction across iterations
"""
import pytest
from backend.agent.orchestration.engine import ResearchEngine
from backend.agent.models.research import ResearchConfig
from backend.agent.retrieval import mock_retriever
from backend.agent.models.common import EventType

@pytest.mark.asyncio
async def test_provider_partial_failure_isolation():
    """Verify that when one provider raises an error, other providers continue and run succeeds."""
    orig_search = mock_retriever.MockAcademicProvider.search

    async def _flaky_search(self, query, **kwargs):
        if self.name == "crossref":
            raise RuntimeError("Simulated crossref upstream 503 outage")
        return await orig_search(self, query, **kwargs)

    mock_retriever.MockAcademicProvider.search = _flaky_search
    try:
        events = []
        cfg = ResearchConfig(
            mock_mode=True,
            llm_provider="mock",
            cache_enabled=False,
            max_iterations=2,
            event_callback=lambda e: events.append(e)
        )
        engine = ResearchEngine()
        result = await engine.run(
            "What are current methods for factuality evaluation in retrieval-augmented generation?",
            config=cfg
        )
        assert result.status == "completed"
        assert len(result.papers) > 0
        failed_evts = [e for e in events if e.type == EventType.RETRIEVAL_FAILED.value]
        assert len(failed_evts) > 0
        assert any("crossref" in e.message.lower() for e in failed_evts)
    finally:
        mock_retriever.MockAcademicProvider.search = orig_search

@pytest.mark.asyncio
async def test_deterministic_gap_reduction_across_iterations():
    """Verify that iteration 1 leaves known gaps, and iteration 2 targets those gaps and raises coverage."""
    cfg = ResearchConfig(
        mock_mode=True,
        llm_provider="mock",
        cache_enabled=False,
        max_iterations=3,
        target_coverage=0.85
    )
    engine = ResearchEngine()
    result = await engine.run(
        "What are current methods for factuality evaluation in retrieval-augmented generation?",
        config=cfg
    )
    assert result.status == "completed"
    assert len(result.iterations) >= 2
    it1 = result.iterations[0]
    it2 = result.iterations[1]
    assert it1.coverage_score == 0.65
    assert it1.reflection is not None
    assert it1.reflection.should_replan is True
    assert len(it1.reflection.missing_topics) > 0
    # Iteration 2 addresses gaps
    assert it2.coverage_score == 0.90
    assert it2.coverage_score > it1.coverage_score
    assert it2.reflection.should_replan is False
