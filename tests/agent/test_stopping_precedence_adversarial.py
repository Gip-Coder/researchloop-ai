"""
Exhaustive adversarial test suite validating Section 3 requirements:
- Case A: Successful completion (target coverage met, critic satisfied)
- Case B: Target coverage met BUT critic dissatisfied (precedence & accurate qualification)
- Case C: No new papers -> diminishing returns detected
- Case D: Repeated gaps -> stagnation detected
- Case E: Max iterations reached with material gaps remaining -> marked and qualified
- Case F: Useful iteration recovers and addresses initial gap
- Case G: Contradictory condition combinations with deterministic precedence
"""
import pytest
from backend.agent.orchestration.engine import ResearchEngine
from backend.agent.models.research import ResearchConfig
from backend.agent.models.paper import Paper
from backend.agent.models.reflection import Reflection
from backend.agent.retrieval.base import AcademicSource
from backend.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_case_a_successful_completion():
    """Case A: Coverage meets target, critic confirms sufficient evidence, terminates successfully."""
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
    assert result.coverage_score >= 0.85
    assert result.stop_reason == "target_coverage_reached"
    assert len(result.iterations) >= 2
    assert result.iterations[-1].reflection.should_replan is False


@pytest.mark.asyncio
async def test_case_b_target_coverage_met_but_critic_dissatisfied():
    """Case B: Target coverage is met numerically, but critic explicitly identifies material gaps.
    Tests precedence: Target coverage takes precedence for loop termination, but stopping_reason
    is correctly recorded and remaining reflection gaps are preserved in final result."""
    orig_ref = MockLLMProvider._mock_reflection

    def _dissatisfied_high_coverage(self, prompt, model_cls):
        return model_cls.model_validate({
            "coverage_score": 0.92,
            "relevance_score": 0.90,
            "missing_topics": ["Nuanced long-tail failure mode analysis"],
            "weak_areas": ["Edge case benchmarks"],
            "contradictions": [],
            "outdated_areas": [],
            "recommended_queries": ["long-tail RAG failures"],
            "should_replan": True,
            "reason": "High breadth achieved but critic notes long-tail failure modes remain unrepresented.",
            "evaluation_type": "llm_critic"
        })

    MockLLMProvider._mock_reflection = _dissatisfied_high_coverage
    try:
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
        assert result.stop_reason == "target_coverage_reached"
        assert result.reflection is not None
        assert "Nuanced long-tail failure mode analysis" in result.reflection.missing_topics
    finally:
        MockLLMProvider._mock_reflection = orig_ref


@pytest.mark.asyncio
async def test_case_c_diminishing_returns_no_new_papers():
    """Case C: Subsequent iteration retrieves no new relevant papers -> diminishing returns stops pipeline."""
    cfg = ResearchConfig(
        mock_mode=True,
        llm_provider="mock",
        cache_enabled=False,
        max_iterations=4,
        target_coverage=0.99,  # Impossibly high
        min_new_relevant_papers=999  # Triggers diminishing returns on iter 2
    )
    engine = ResearchEngine()
    result = await engine.run(
        "What are current methods for factuality evaluation in retrieval-augmented generation?",
        config=cfg
    )
    assert result.status == "completed"
    assert result.stop_reason == "diminishing_returns_no_new_papers"
    assert len(result.iterations) == 2


@pytest.mark.asyncio
async def test_case_d_repeated_stagnant_gaps():
    """Case D: Critic identifies exact same unresolved gaps across consecutive iterations with no progress."""
    orig_ref = MockLLMProvider._mock_reflection

    def _stagnant_reflection(self, prompt, model_cls):
        return model_cls.model_validate({
            "coverage_score": 0.50,
            "relevance_score": 0.80,
            "missing_topics": ["Specific Unresolved Gap A", "Specific Unresolved Gap B"],
            "weak_areas": [],
            "contradictions": [],
            "outdated_areas": [],
            "recommended_queries": ["query A", "query B"],
            "should_replan": True,
            "reason": "Unresolved gaps remain stagnant.",
            "evaluation_type": "llm_critic"
        })

    MockLLMProvider._mock_reflection = _stagnant_reflection
    try:
        cfg = ResearchConfig(
            mock_mode=True,
            llm_provider="mock",
            cache_enabled=False,
            max_iterations=5,
            target_coverage=0.95
        )
        engine = ResearchEngine()
        result = await engine.run(
            "What are current methods for factuality evaluation in retrieval-augmented generation?",
            config=cfg
        )
        assert result.status == "completed"
        assert result.stop_reason in ("stagnant_repeated_gaps", "diminishing_returns_no_new_papers")
        assert len(result.iterations) <= 3
    finally:
        MockLLMProvider._mock_reflection = orig_ref


@pytest.mark.asyncio
async def test_case_e_max_iterations_reached_incomplete():
    """Case E: Max iterations reached when iterations vary gaps but remain unsatisfied."""
    iter_counter = 0
    orig_ref = MockLLMProvider._mock_reflection

    def _varying_gaps_reflection(self, prompt, model_cls):
        nonlocal iter_counter
        iter_counter += 1
        return model_cls.model_validate({
            "coverage_score": 0.40,
            "relevance_score": 0.60,
            "missing_topics": [f"Unique Missing Gap Phase {iter_counter}"],
            "weak_areas": ["General gaps"],
            "contradictions": [],
            "outdated_areas": [],
            "recommended_queries": [f"query {iter_counter}"],
            "should_replan": True,
            "reason": f"Insufficient evidence in phase {iter_counter}.",
            "evaluation_type": "llm_critic"
        })

    MockLLMProvider._mock_reflection = _varying_gaps_reflection
    try:
        cfg = ResearchConfig(
            mock_mode=True,
            llm_provider="mock",
            cache_enabled=False,
            max_iterations=2,
            target_coverage=0.90,
            min_new_relevant_papers=0
        )
        engine = ResearchEngine()
        result = await engine.run(
            "What are current methods for factuality evaluation in retrieval-augmented generation?",
            config=cfg
        )
        assert result.status == "completed"
        assert result.stop_reason == "max_iterations_reached"
        assert result.coverage_score == 0.40
        assert len(result.iterations) == 2
    finally:
        MockLLMProvider._mock_reflection = orig_ref


@pytest.mark.asyncio
async def test_case_f_useful_iteration_recovery():
    """Case F: Iteration 1 identifies a gap, Iteration 2 retrieves evidence addressing it and raises coverage."""
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
    assert len(result.iterations) >= 2
    it1 = result.iterations[0]
    it2 = result.iterations[1]
    assert it1.coverage_score < it2.coverage_score
    assert len(it1.reflection.missing_topics) > 0
    assert len(it2.reflection.missing_topics) == 0


@pytest.mark.asyncio
async def test_case_g_deterministic_precedence():
    """Case G: Contradictory condition combinations test strict precedence:
    If coverage_score >= target_coverage AND max_iterations is reached simultaneously,
    Condition A (target_coverage_reached) evaluates first."""
    orig_ref = MockLLMProvider._mock_reflection

    def _high_on_iter_1(self, prompt, model_cls):
        return model_cls.model_validate({
            "coverage_score": 0.95,
            "relevance_score": 0.95,
            "missing_topics": [],
            "weak_areas": [],
            "contradictions": [],
            "outdated_areas": [],
            "recommended_queries": [],
            "should_replan": False,
            "reason": "Exhaustive coverage in first pass.",
            "evaluation_type": "llm_critic"
        })

    MockLLMProvider._mock_reflection = _high_on_iter_1
    try:
        cfg = ResearchConfig(
            mock_mode=True,
            llm_provider="mock",
            cache_enabled=False,
            max_iterations=1,
            target_coverage=0.85
        )
        engine = ResearchEngine()
        result = await engine.run(
            "What are current methods for factuality evaluation in retrieval-augmented generation?",
            config=cfg
        )
        assert result.status == "completed"
        assert result.stop_reason == "target_coverage_reached"
    finally:
        MockLLMProvider._mock_reflection = orig_ref
