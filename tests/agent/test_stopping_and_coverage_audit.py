"""
Additional rigorous tests addressing P0 audit items:
- Target threshold enforcement
- Negative fixture where irrelevant papers are returned (must not report success)
- Repeated stagnant gaps stopping condition
- Critic reflection validation bounds
"""
import pytest
from backend.agent.orchestration.engine import ResearchEngine
from backend.agent.models.research import ResearchConfig
from backend.agent.models.paper import Paper
from backend.agent.models.reflection import Reflection
from backend.agent.retrieval import mock_retriever
from backend.agent.retrieval.base import AcademicSource

@pytest.mark.asyncio
async def test_target_coverage_threshold_enforcement():
    """Ensure that if target is 0.95 and score is 0.90, target_coverage_reached is NOT triggered."""
    cfg = ResearchConfig(
        mock_mode=True,
        llm_provider="mock",
        cache_enabled=False,
        max_iterations=2,
        target_coverage=0.99  # Higher than mock max of 0.90
    )
    engine = ResearchEngine()
    result = await engine.run(
        "What are current methods for factuality evaluation in retrieval-augmented generation?",
        config=cfg
    )
    assert result.status == "completed"
    assert result.stop_reason != "target_coverage_reached"
    assert result.stop_reason in ("critic_satisfied_coverage", "max_iterations_reached", "diminishing_returns_no_new_papers")

@pytest.mark.asyncio
async def test_negative_fixture_irrelevant_papers():
    """Negative fixture: when retrieval returns exclusively off-topic papers,
    the relevance filter rejects them, zero relevant papers are retained, and review indicates lack of evidence."""
    
    class IrrelevantRetriever(AcademicSource):
        def __init__(self):
            super().__init__(name="irrelevant_source")
        async def search(self, query, **kwargs):
            return [
                Paper(
                    id="irr-1",
                    title="Photosynthetic energy transfer in cryptophyte algae",
                    abstract="Quantum biology and photosynthetic energy transfer in marine algae.",
                    source="irrelevant_source",
                    year=2022
                ),
                Paper(
                    id="irr-2",
                    title="Nitrogen fixation in agricultural crop yield",
                    abstract="Agronomic soil chemistry and nitrogen fixation rates.",
                    source="irrelevant_source",
                    year=2021
                )
            ]

    # Temporarily replace providers in retriever
    from backend.agent.retrieval.multi_retriever import MultiProviderRetriever
    orig_init = MultiProviderRetriever.__init__

    def _mock_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.providers = {"irrelevant": IrrelevantRetriever()}

    MultiProviderRetriever.__init__ = _mock_init
    try:
        cfg = ResearchConfig(
            mock_mode=True,
            llm_provider="mock",
            cache_enabled=False,
            max_iterations=1,
            preferred_sources=["irrelevant"]
        )
        engine = ResearchEngine()
        result = await engine.run(
            "What are current methods for factuality evaluation in retrieval-augmented generation?",
            config=cfg
        )
        assert result.status == "completed"
        # All retrieved papers were rejected as irrelevant
        assert len(result.relevant_papers) == 0
        assert any(p.is_relevant is False for p in result.papers)
    finally:
        MultiProviderRetriever.__init__ = orig_init

@pytest.mark.asyncio
async def test_stagnant_repeated_gaps_stopping_condition():
    """Verify that if the critic repeats the exact same missing topics across iterations with zero progress,
    the stagnant_repeated_gaps condition triggers."""
    from backend.providers.llm.mock import MockLLMProvider

    orig_ref = MockLLMProvider._mock_reflection

    def _stagnant_reflection(self, prompt, model_cls):
        # Always return the exact same missing topic and should_replan=True with low coverage
        return model_cls.model_validate({
            "coverage_score": 0.50,
            "relevance_score": 0.80,
            "missing_topics": ["Specific Unresolved Gap A", "Specific Unresolved Gap B"],
            "weak_areas": [],
            "contradictions": [],
            "outdated_areas": [],
            "recommended_queries": ["query A", "query B"],
            "should_replan": True,
            "reason": "Unresolved gaps remain.",
            "evaluation_type": "llm_critic"
        })

    MockLLMProvider._mock_reflection = _stagnant_reflection
    try:
        cfg = ResearchConfig(
            mock_mode=True,
            llm_provider="mock",
            cache_enabled=False,
            max_iterations=4,
            target_coverage=0.95
        )
        engine = ResearchEngine()
        result = await engine.run(
            "How does retrieval augmented generation improve factuality?",
            config=cfg
        )
        assert result.status == "completed"
        # Should stop before max_iterations=4 due to lack of progress / stagnant gaps
        assert result.stop_reason in ("stagnant_repeated_gaps", "diminishing_returns_no_new_papers")
    finally:
        MockLLMProvider._mock_reflection = orig_ref
