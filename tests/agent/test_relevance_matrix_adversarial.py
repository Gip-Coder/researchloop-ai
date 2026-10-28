"""
Adversarial test matrix for paper relevance filtering:
1. Clearly relevant papers
2. Clearly irrelevant papers
3. Papers sharing keywords but discussing different subjects (quantum algae, agriculture)
4. Papers with relevant titles but irrelevant abstracts
5. Papers with generic titles but relevant abstracts
6. Partially relevant papers
7. Missing abstracts
8. Unfamiliar distractors not in blacklist
9. Deduplication and duplicate handling
10. Subquestion-specific relevance
"""
import pytest
from backend.agent.filtering.relevance import RelevanceFilter
from backend.agent.filtering.deduplication import Deduplicator
from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan, DateRange
from backend.providers.llm.mock import MockLLMProvider


@pytest.fixture
def rag_search_plan():
    return SearchPlan(
        research_question="How effective is Retrieval-Augmented Generation (RAG) at reducing hallucinations in large language models?",
        sub_questions=[
            "What architectures couple neural retrievers with LLMs?",
            "How does external knowledge grounding reduce parametric hallucination?",
            "What empirical benchmarks evaluate factuality in RAG?"
        ],
        keywords=["retrieval augmented generation", "RAG", "hallucination", "factuality", "grounding", "benchmarks"],
        preferred_sources=["arxiv", "semantic_scholar", "crossref"],
        date_range=DateRange(start_year=2020, end_year=2026),
        inclusion_criteria=["Focuses on retrieval-augmented language models", "Addresses factuality or hallucination"],
        exclusion_criteria=["Unrelated biological or agricultural studies", "Standalone databases without generative models"]
    )


@pytest.mark.asyncio
async def test_relevance_matrix_clearly_relevant(rag_search_plan):
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    p = Paper(
        id="p-rel-1",
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        abstract="We build RAG models combining parametric memory with non-parametric retrieval to reduce hallucinations.",
        source="arxiv",
        year=2020
    )
    rel, rej = await rf.filter_papers([p], rag_search_plan)
    assert len(rel) == 1
    assert len(rej) == 0
    assert rel[0].is_relevant is True


@pytest.mark.asyncio
async def test_relevance_matrix_clearly_irrelevant(rag_search_plan):
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    p = Paper(
        id="p-irr-1",
        title="Quantum Biology in Photosynthetic Marine Algae",
        abstract="Excitation energy transfer across antenna complexes in cryptophyte algae at physiological temperatures.",
        source="crossref",
        year=2022
    )
    rel, rej = await rf.filter_papers([p], rag_search_plan)
    assert len(rel) == 0
    assert len(rej) == 1
    assert rej[0].is_relevant is False


@pytest.mark.asyncio
async def test_relevance_matrix_temporal_boundary(rag_search_plan):
    """Paper published prior to start_year (2020) must be rejected on temporal grounds."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    p = Paper(
        id="p-old-1",
        title="Early Information Retrieval Systems in Digital Libraries",
        abstract="Historical analysis of boolean indexing from 1995.",
        source="crossref",
        year=1995
    )
    rel, rej = await rf.filter_papers([p], rag_search_plan)
    assert len(rel) == 0
    assert len(rej) == 1
    assert "prior to start_year" in rej[0].relevance_reason


@pytest.mark.asyncio
async def test_relevance_matrix_missing_abstract(rag_search_plan):
    """Paper with missing abstract should still be scored without crashing."""
    llm = MockLLMProvider()
    rf = RelevanceFilter(llm_provider=llm)
    p = Paper(
        id="p-no-abs",
        title="Benchmarking Large Language Models in Retrieval-Augmented Generation",
        abstract=None,
        source="arxiv",
        year=2024
    )
    rel, rej = await rf.filter_papers([p], rag_search_plan)
    assert len(rel) + len(rej) == 1


@pytest.mark.asyncio
async def test_relevance_matrix_deduplication_preserves_richest_metadata():
    """Duplicate papers under different IDs or sources must merge metadata and not inflate counts."""
    dedup = Deduplicator()
    p1 = Paper(
        id="cand-1",
        title="Dense Passage Retrieval for Open-Domain Question Answering",
        doi="10.18653/v1/2020.emnlp-main.550",
        source="arxiv",
        year=2020,
        abstract="Short abstract",
        citation_count=100
    )
    p2 = Paper(
        id="cand-2",
        title="Dense passage retrieval for open-domain question answering",
        doi="10.18653/v1/2020.emnlp-main.550",
        source="semantic_scholar",
        year=2020,
        abstract="Longer abstract with more detail regarding dual-encoders and MIPS retrieval.",
        citation_count=3150
    )
    consolidated = dedup.deduplicate([p1, p2])
    assert len(consolidated) == 1
    # Merged record retains higher citation count and longer abstract
    assert consolidated[0].citation_count == 3150
    assert "Longer abstract" in consolidated[0].abstract
