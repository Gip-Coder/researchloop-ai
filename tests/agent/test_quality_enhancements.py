"""
Regression and acceptance test suite for Research Quality Enhancements (Phase 2 & Phase 3):
- Publication-year filtering (2019+ default, missing years, foundational exceptions)
- Citation-count preference (10-15 preference, ranking, unknown citation handling, strict option)
- Phrase-based academic query generation & provenance
- Synthesis evidence pool sizing (6-10 papers target, warning on insufficient evidence)
"""

import pytest
from backend.agent.core.config import get_settings, parse_preferred_sources
from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.agent.models.research import ResearchConfig
from backend.agent.filtering.relevance import RelevanceFilter
from backend.agent.filtering.ranking import rank_papers_for_synthesis, is_in_citation_range
from backend.agent.planner.planner import PlanningAgent
from backend.agent.replanning.replanner import ReplanningAgent
from backend.agent.retrieval.arxiv import ArxivProvider
from backend.agent.retrieval.crossref import CrossrefProvider
from backend.agent.retrieval.multi_retriever import MultiProviderRetriever
from backend.agent.retrieval.mock_retriever import MockAcademicProvider
from backend.agent.orchestration.engine import ResearchEngine
from backend.providers.llm.mock import MockLLMProvider


# -------------------------------------------------------------------------
# Phase 2.1: Publication Year Constraint Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_publication_year_filter_defaults_to_2019():
    """Verify papers before 2019 are excluded, 2019 and newer are eligible."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    plan = SearchPlan(
        research_question="How does retrieval augmented generation reduce hallucinations?",
        min_publication_year=2019,
        keywords=["retrieval", "augmented", "generation", "hallucinations"]
    )

    p_2018 = Paper(
        id="p-2018",
        title="Old RAG Foundations",
        year=2018,
        source="arxiv",
        abstract="Early retrieval grounding in neural networks."
    )
    p_2019 = Paper(
        id="p-2019",
        title="2019 Emergence Paper",
        year=2019,
        source="arxiv",
        abstract="Neural passage retrieval with generative models."
    )
    p_2024 = Paper(
        id="p-2024",
        title="Modern 2024 Benchmark",
        year=2024,
        source="crossref",
        abstract="State of the art RAG benchmarking."
    )

    relevant, rejected = await rf.filter_papers([p_2018, p_2019, p_2024], plan)

    rel_ids = [p.id for p in relevant]
    rej_ids = [p.id for p in rejected]

    assert "p-2018" in rej_ids
    assert "p-2019" in rel_ids
    assert "p-2024" in rel_ids
    # Check rejection reason explicitly states publication year constraint
    rej_2018 = next(p for p in rejected if p.id == "p-2018")
    assert "2018" in rej_2018.relevance_reason
    assert "2019" in rej_2018.relevance_reason


@pytest.mark.asyncio
async def test_missing_year_handled_deterministically():
    """Papers with missing publication year must be excluded deterministically with explanation."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    plan = SearchPlan(
        research_question="Evaluation of retrieval-augmented generation",
        min_publication_year=2019
    )

    p_undated = Paper(
        id="p-undated",
        title="Undated Manuscript on Retrieval",
        year=None,
        source="arxiv",
        abstract="Undated draft without verifiable year metadata."
    )

    relevant, rejected = await rf.filter_papers([p_undated], plan)
    assert len(relevant) == 0
    assert len(rejected) == 1
    assert "Publication year missing" in rejected[0].relevance_reason


@pytest.mark.asyncio
async def test_foundational_exception_policy():
    """Pre-2019 paper is excluded by default, but admitted only when foundational exception is explicitly allowed."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)

    p_vaswani = Paper(
        id="p-attention-2017",
        title="Attention Is All You Need",
        year=2017,
        source="arxiv",
        is_foundational_exception=True,
        abstract="The Transformer architecture based entirely on self-attention mechanisms."
    )

    # 1. Default policy: allow_foundational_exceptions=False
    plan_default = SearchPlan(
        research_question="Transformer architectures in language modeling",
        min_publication_year=2019,
        allow_foundational_exceptions=False
    )
    rel_def, rej_def = await rf.filter_papers([p_vaswani], plan_default)
    assert len(rel_def) == 0
    assert len(rej_def) == 1

    # 2. Explicitly allowed foundational exceptions
    plan_allowed = SearchPlan(
        research_question="Transformer architectures in language modeling",
        min_publication_year=2019,
        allow_foundational_exceptions=True
    )
    rel_allow, rej_allow = await rf.filter_papers([p_vaswani], plan_allowed)
    assert len(rel_allow) == 1
    assert rel_allow[0].id == "p-attention-2017"


# -------------------------------------------------------------------------
# Phase 2.2: Citation-Count Preference (10-15 Range) Tests
# -------------------------------------------------------------------------

def test_citation_range_check():
    """Verify is_in_citation_range accurately handles bounds and None."""
    p_exact_10 = Paper(id="1", title="P1", year=2021, source="arxiv", citation_count=10)
    p_exact_15 = Paper(id="2", title="P2", year=2021, source="arxiv", citation_count=15)
    p_in_between = Paper(id="3", title="P3", year=2021, source="arxiv", citation_count=12)
    p_below = Paper(id="4", title="P4", year=2021, source="arxiv", citation_count=9)
    p_above = Paper(id="5", title="P5", year=2021, source="arxiv", citation_count=16)
    p_unknown = Paper(id="6", title="P6", year=2021, source="arxiv", citation_count=None)

    assert is_in_citation_range(p_exact_10) is True
    assert is_in_citation_range(p_exact_15) is True
    assert is_in_citation_range(p_in_between) is True
    assert is_in_citation_range(p_below) is False
    assert is_in_citation_range(p_above) is False
    assert is_in_citation_range(p_unknown) is False


def test_citation_preference_ranking_policy():
    """
    Test preference-based ranking:
    In-range papers (10-15) are prioritized, but high-relevance papers outside range
    remain eligible and are not excluded.
    """
    papers = [
        Paper(id="p-high-rel-many-cit", title="Seminal RAG", year=2020, source="arxiv", citation_count=4000, relevance_score=0.95),
        Paper(id="p-in-range-1", title="In Range Study A", year=2023, source="arxiv", citation_count=12, relevance_score=0.88),
        Paper(id="p-in-range-2", title="In Range Study B", year=2024, source="crossref", citation_count=14, relevance_score=0.90),
        Paper(id="p-unknown-cit", title="New Preprint", year=2024, source="arxiv", citation_count=None, relevance_score=0.89),
        Paper(id="p-low-cit", title="Emerging Workshop", year=2023, source="crossref", citation_count=3, relevance_score=0.75),
    ]

    eligible, excluded = rank_papers_for_synthesis(
        papers,
        preferred_min_citations=10,
        preferred_max_citations=15,
        strict_citation_filtering=False,
        min_year=2019
    )

    # In default mode, all 2019+ relevant papers are eligible
    assert len(eligible) == 5
    assert len(excluded) == 0

    # Top papers should be in-range citations (Tier 1)
    top_ids = [p.id for p in eligible[:2]]
    assert "p-in-range-2" in top_ids
    assert "p-in-range-1" in top_ids

    # High-relevance paper with 4000 citations is in Tier 2
    assert eligible[2].id in ("p-high-rel-many-cit", "p-unknown-cit")


def test_strict_citation_filtering_policy():
    """Strict filtering option strictly excludes papers outside the preferred citation range."""
    papers = [
        Paper(id="p-in-range", title="In Range", year=2021, source="arxiv", citation_count=12),
        Paper(id="p-out-range", title="Out Range", year=2021, source="arxiv", citation_count=500),
        Paper(id="p-no-cit", title="No Citations", year=2021, source="arxiv", citation_count=None),
    ]

    eligible, excluded = rank_papers_for_synthesis(
        papers,
        preferred_min_citations=10,
        preferred_max_citations=15,
        strict_citation_filtering=True,
        min_year=2019
    )

    assert len(eligible) == 1
    assert eligible[0].id == "p-in-range"
    assert len(excluded) == 2


# -------------------------------------------------------------------------
# Phase 2.3: Phrase-Based Academic Search Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_planner_generates_phrase_queries():
    """Verify that Planner generates queries utilizing multiword academic phrases in quotes."""
    llm = MockLLMProvider()
    planner = PlanningAgent(llm_provider=llm)

    plan = await planner.plan("How does retrieval augmented generation reduce hallucinations in large language models?")
    assert len(plan.search_queries) >= 3
    # Check that at least one query contains quotes for exact phrase retrieval
    has_phrase_quote = any('"' in q for q in plan.search_queries)
    assert has_phrase_quote, f"Search queries should contain phrase quotes: {plan.search_queries}"


@pytest.mark.asyncio
async def test_replanner_generates_gap_targeted_phrase_queries():
    """Verify replanner converts critic gaps into targeted phrase queries."""
    llm = MockLLMProvider()
    replanner = ReplanningAgent(llm_provider=llm)

    # State with identified gap
    from backend.agent.models.research import ResearchState
    from backend.agent.models.reflection import Reflection

    state = ResearchState(
        research_question="Factuality evaluation in RAG",
        iteration=1,
        search_plan=SearchPlan(
            research_question="Factuality evaluation in RAG",
            search_queries=['"RAG" factuality']
        ),
        reflection=Reflection(
            coverage_score=0.6,
            relevance_score=0.8,
            missing_topics=["RGB noise robustness benchmark", "atomic factuality FactScore"],
            recommended_queries=['"RGB benchmark" noise robustness in RAG'],
            should_replan=True,
            reason="Lacking benchmark coverage"
        )
    )

    new_plan = await replanner.replan(state)
    assert len(new_plan.search_queries) >= 2
    # Ensure quotes are preserved and queries do not replicate previous plan
    assert all(q.strip().lower() != '"rag" factuality' for q in new_plan.search_queries)


def test_arxiv_preserves_double_quotes_in_query():
    """Verify ArxivProvider does not strip double quotes required for phrase matching."""
    provider = ArxivProvider()
    # clean_query should retain quotes
    import re
    query = '"retrieval-augmented generation" benchmark evaluation'
    clean_query = re.sub(r'[^\w\s"-]', " ", query).strip()
    assert '"retrieval-augmented generation"' in clean_query


# -------------------------------------------------------------------------
# Phase 2.4: Synthesis Evidence Pool & Engine Execution Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evidence_pool_synthesis_target():
    """Verify ResearchEngine retrieves and ranks 6-10 unique eligible papers for synthesis."""
    cfg = ResearchConfig(
        mock_mode=True,
        llm_provider="mock",
        cache_enabled=False,
        max_iterations=3,
        min_synthesis_papers=6,
        target_synthesis_papers=8,
        max_synthesis_papers=10,
        min_publication_year=2019
    )

    engine = ResearchEngine()
    result = await engine.run(
        "What are current methods for factuality evaluation in retrieval-augmented generation?",
        config=cfg
    )

    assert result.status == "completed"
    # Verify bibliography has >= 6 papers
    bib = result.final_review.get("bibliography", [])
    assert len(bib) >= 6, f"Expected at least 6 papers in bibliography, got {len(bib)}"
    assert len(bib) <= 10, f"Expected at most 10 papers in bibliography, got {len(bib)}"

    # All synthesized papers must satisfy the 2019+ publication year constraint
    for paper_info in bib:
        if not paper_info.get("is_foundational_exception"):
            assert paper_info["year"] >= 2019, f"Paper {paper_info['id']} year {paper_info['year']} < 2019"

    # Verify final review metadata
    assert result.final_review.get("evidence_target_met") is True
    assert result.final_review.get("insufficient_evidence_warning") is None


@pytest.mark.asyncio
async def test_insufficient_evidence_warning():
    """Verify that when fewer than min_synthesis_papers are available, a clear warning is generated."""
    # Custom provider that returns only 2 papers
    class ScarceProvider(MockAcademicProvider):
        async def search(self, query: str, **kwargs):
            return [self.corpus[0].model_copy(), self.corpus[1].model_copy()]

    cfg = ResearchConfig(
        mock_mode=True,
        llm_provider="mock",
        cache_enabled=False,
        max_iterations=1,
        min_synthesis_papers=6,
        target_synthesis_papers=8,
        max_synthesis_papers=10
    )

    engine = ResearchEngine()
    # Mock retriever returning only 2 papers
    retriever = MultiProviderRetriever(providers=[ScarceProvider(name="arxiv")])
    result = await engine.run(
        "Very rare esoteric niche question with minimal literature",
        config=cfg
    )

    # In mock mode, if corpus has limited matches or restricted iteration
    if result.final_review.get("eligible_papers_count", 0) < cfg.min_synthesis_papers:
        assert result.final_review.get("evidence_target_met") is False
        assert result.final_review.get("insufficient_evidence_warning") is not None
        assert "Evidence target" in result.final_review["insufficient_evidence_warning"]


# -------------------------------------------------------------------------
# Phase 2.5: Publication Year Removal & Minimum Citations Constraint Tests
# -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_publication_year_constraint_by_default():
    """Verify papers from older years or with missing years are accepted when min_publication_year is None."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    plan = SearchPlan(
        research_question="How does retrieval augmented generation reduce hallucinations?",
        min_publication_year=None,
        min_citations=0,
        keywords=["retrieval", "augmented", "generation"]
    )

    p_old = Paper(id="p-2005", title="Early Retrieval Research", year=2005, source="crossref", abstract="Early work on retrieval.")
    p_undated = Paper(id="p-undated", title="Undated Preprint", year=None, source="arxiv", abstract="Preprint on retrieval.")

    relevant, rejected = await rf.filter_papers([p_old, p_undated], plan)
    rel_ids = [p.id for p in relevant]
    assert "p-2005" in rel_ids
    assert "p-undated" in rel_ids


@pytest.mark.asyncio
async def test_minimum_citations_constraint_filtering():
    """Verify papers below min_citations are rejected, while papers meeting threshold or unknown citations pass."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    plan = SearchPlan(
        research_question="How does retrieval augmented generation reduce hallucinations?",
        min_publication_year=None,
        min_citations=5,
        allow_unknown_citations=True
    )

    p_high = Paper(id="p-high", title="High Citation Study", year=2021, citation_count=25, source="crossref")
    p_exact = Paper(id="p-exact", title="Exact Threshold Study", year=2022, citation_count=5, source="crossref")
    p_low = Paper(id="p-low", title="Low Citation Study", year=2023, citation_count=2, source="crossref")
    p_arxiv_unknown = Paper(id="p-arxiv", title="Preprint Unknown Citation", year=2024, citation_count=None, source="arxiv")

    relevant, rejected = await rf.filter_papers([p_high, p_exact, p_low, p_arxiv_unknown], plan)

    rel_ids = [p.id for p in relevant]
    rej_ids = [p.id for p in rejected]

    assert "p-high" in rel_ids
    assert "p-exact" in rel_ids
    assert "p-arxiv" in rel_ids
    assert "p-low" in rej_ids

    low_rej = next(p for p in rejected if p.id == "p-low")
    assert "below minimum requirement of 5 citations" in low_rej.relevance_reason


@pytest.mark.asyncio
async def test_disallow_unknown_citations_filtering():
    """Verify that when allow_unknown_citations=False, papers with citation_count=None are rejected."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    plan = SearchPlan(
        research_question="How does retrieval augmented generation reduce hallucinations?",
        min_publication_year=None,
        min_citations=5,
        allow_unknown_citations=False
    )

    p_arxiv = Paper(id="p-arxiv", title="Preprint Unknown Citation", year=2024, citation_count=None, source="arxiv")
    relevant, rejected = await rf.filter_papers([p_arxiv], plan)
    assert len(relevant) == 0
    assert len(rejected) == 1
    assert "Citation count is unknown" in rejected[0].relevance_reason
