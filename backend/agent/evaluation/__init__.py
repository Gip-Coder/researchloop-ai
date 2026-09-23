"""
Evaluation and benchmark comparison package.
"""

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
    BenchmarkComparisonResult,
    compare_against_benchmark,
)

__all__ = [
    "compute_coverage",
    "compute_relevance",
    "compute_paper_recall",
    "compute_topic_coverage",
    "compute_citation_distribution",
    "compute_coherence",
    "CuratedBenchmarkReview",
    "BenchmarkComparisonResult",
    "compare_against_benchmark",
]
