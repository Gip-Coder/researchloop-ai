"""
Tests for evaluation metrics and benchmark review comparison.
"""

from __future__ import annotations

import pytest
from backend.agent.evaluation.metrics import (
    compute_coverage,
    compute_relevance,
    compute_paper_recall,
    compute_topic_coverage,
    compute_citation_distribution,
    compute_coherence,
)
from backend.agent.evaluation.benchmark import (
    CuratedBenchmarkReview,
    compare_against_benchmark,
)
from backend.agent.models.paper import Paper
from backend.agent.models.synthesis import Synthesis, Theme, PaperAnalysis
from backend.agent.models.research import ResearchState, ResearchResult
from backend.agent.models.reflection import Reflection


def test_compute_coverage():
    state = ResearchState(
        research_question="Sample question",
        reflection=Reflection(
            coverage_score=0.77,
            relevance_score=0.85,
            reason="Good initial coverage."
        )
    )
    assert compute_coverage(state) == 0.77


def test_compute_relevance():
    papers = [
        Paper(id="p1", title="Title 1", source="arxiv", relevance_score=0.9),
        Paper(id="p2", title="Title 2", source="arxiv", relevance_score=0.7),
    ]
    assert compute_relevance(papers) == 0.8


def test_compute_paper_recall():
    papers = [
        Paper(id="p1", title="Retrieval-Augmented Generation for NLP Tasks", doi="10.5555/3495724.3496517", source="arxiv"),
        Paper(id="p2", title="Dense Passage Retrieval", doi="10.18653/v1/2020.emnlp-main.550", source="arxiv"),
    ]
    ground_truth = [
        "10.5555/3495724.3496517",
        "Dense Passage Retrieval",
        "Missing Third Paper"
    ]
    recall = compute_paper_recall(papers, ground_truth)
    assert recall == round(2 / 3, 3)


def test_compute_topic_coverage():
    themes = [
        Theme(id="t1", title="Neural Dense Retrieval", description="Passage representations", paper_ids=["p1"], key_findings=["finding 1"]),
        Theme(id="t2", title="Factuality and Hallucination", description="Evaluating truthfulness", paper_ids=["p2"], key_findings=["finding 2"]),
    ]
    expected = ["Retrieval", "Hallucination", "Quantum Mechanics"]
    cov = compute_topic_coverage(themes, expected)
    assert cov == round(2 / 3, 3)


def test_compute_citation_distribution():
    papers = [
        Paper(id="p1", title="P1", source="arxiv", citation_count=100),
        Paper(id="p2", title="P2", source="arxiv", citation_count=50),
        Paper(id="p3", title="P3", source="arxiv", citation_count=150),
    ]
    stats = compute_citation_distribution(papers)
    assert stats["total_citations"] == 300
    assert stats["mean_citations"] == 100.0
    assert stats["median_citations"] == 100.0
    assert stats["max_citations"] == 150


def test_compute_coherence():
    # Coherent synthesis: grounded themes, agreements, differences, contradictions, gaps, narrative
    synthesis = Synthesis(
        paper_analyses=[
            PaperAnalysis(
                paper_id="p1",
                title="Paper 1",
                research_problem="Problem 1",
                methodology="Method 1",
                contribution="Contrib 1",
                limitations=["Lim 1"],
                relevance="Rel 1",
                key_findings=["Finding 1"]
            ),
            PaperAnalysis(
                paper_id="p2",
                title="Paper 2",
                research_problem="Problem 2",
                methodology="Method 2",
                contribution="Contrib 2",
                limitations=["Lim 2"],
                relevance="Rel 2",
                key_findings=["Finding 2"]
            )
        ],
        themes=[
            Theme(
                id="t1",
                title="Theme 1",
                description="Desc 1",
                paper_ids=["p1", "p2"],
                key_findings=["Finding 1", "Finding 2"]
            )
        ],
        agreements=["Consensus on grounding"],
        differences=["Disagreement on chunk size"],
        contradictions=["Contradiction on reranking"],
        methodological_differences=["Dense vs hybrid"],
        trends=["Iterative RAG"],
        research_gaps=["Real-time synchronization"],
        narrative_summary="A comprehensive executive narrative summarizing literature across themes and findings."
    )

    coherence = compute_coherence(synthesis)
    assert 0.8 <= coherence <= 1.0

    # Incoherent / empty synthesis
    assert compute_coherence(None) == 0.0


def test_compare_against_curated_benchmark(sample_curated_benchmark: CuratedBenchmarkReview):
    result = ResearchResult(
        session_id="session-123",
        status="completed",
        research_question="How does retrieval augmented generation improve factuality in large language models?",
        papers=[
            Paper(
                id="p1",
                title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                doi="10.5555/3495724.3496517",
                source="arxiv"
            ),
            Paper(
                id="p2",
                title="Dense Passage Retrieval for Open-Domain Question Answering",
                doi="10.18653/v1/2020.emnlp-main.550",
                source="arxiv"
            ),
            Paper(
                id="p3",
                title="FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long-form Text Generation",
                doi="10.18653/v1/2023.emnlp-main.741",
                source="crossref"
            )
        ],
        relevant_papers=[],
        themes=[
            Theme(
                id="t1",
                title="Dense Retrieval and Knowledge Grounding",
                description="Coupling pre-trained models with dense passage indexes.",
                paper_ids=["p1", "p2"],
                key_findings=[]
            ),
            Theme(
                id="t2",
                title="Benchmarking and Hallucination Evaluation",
                description="Datasets measuring factual consistency and hallucination mitigation.",
                paper_ids=["p3"],
                key_findings=[]
            )
        ],
        synthesis=Synthesis(
            agreements=[
                "External document retrieval reduces factual errors compared to closed-book generators"
            ],
            narrative_summary="RAG enhances factuality across benchmarks."
        ),
        reflection=None,
        coverage_score=0.88,
        stop_reason="target_coverage_reached",
        events=[]
    )

    report = compare_against_benchmark(result, sample_curated_benchmark)

    assert report.paper_recall >= 0.75  # Found 3 of 4 key papers
    assert "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" in report.found_key_papers
    assert report.topic_overlap_score >= 0.75
    assert report.finding_alignment_score > 0.0
    assert "Benchmark Comparison" in report.summary

