"""
Curated benchmark review schemas and comparison module.
Allows validating autonomous agent research results against human-curated ground truth reviews.
"""

from __future__ import annotations

import difflib
import re
from typing import Any
from pydantic import BaseModel, Field

from backend.agent.models.research import ResearchResult
from backend.agent.models.paper import Paper


class CuratedBenchmarkReview(BaseModel):
    """Ground-truth benchmark review created by human researchers."""

    title: str = Field(description="Title of curated literature review")
    research_question: str = Field(description="Target research question")
    key_paper_dois_or_titles: list[str] = Field(
        description="Essential canonical papers that any thorough review must cite"
    )
    expected_topics: list[str] = Field(
        description="Key conceptual themes that must be covered"
    )
    ground_truth_findings: list[str] = Field(
        default_factory=list,
        description="Consensus findings or insights documented in the literature"
    )


class BenchmarkComparisonResult(BaseModel):
    """Evaluation report comparing agent execution against a curated benchmark."""

    paper_recall: float = Field(ge=0.0, le=1.0, description="Proportion of key benchmark papers discovered")
    found_key_papers: list[str] = Field(default_factory=list, description="Benchmark papers successfully retrieved")
    missed_key_papers: list[str] = Field(default_factory=list, description="Benchmark papers missed by retrieval")
    topic_overlap_score: float = Field(ge=0.0, le=1.0, description="Overlap between agent themes and benchmark topics")
    covered_topics: list[str] = Field(default_factory=list, description="Benchmark topics reflected in agent themes")
    missed_topics: list[str] = Field(default_factory=list, description="Benchmark topics absent from agent themes")
    finding_alignment_score: float = Field(ge=0.0, le=1.0, description="Heuristic alignment with ground-truth findings")
    summary: str = Field(description="Summary narrative of comparative evaluation")


def compare_against_benchmark(
    result: ResearchResult,
    benchmark: CuratedBenchmarkReview
) -> BenchmarkComparisonResult:
    """
    Compare agent ResearchResult against human-curated benchmark.
    Computes paper recall, topic overlap, and finding alignment.
    """
    # 1. Paper Recall
    found_papers = []
    missed_papers = []

    retrieved_dois = {
        re.sub(r"^https?://(dx\.)?doi\.org/", "", (p.doi or "").lower().strip())
        for p in result.papers if p.doi
    }
    retrieved_titles = [
        re.sub(r"[^\w\s]", "", p.title.lower()).strip() for p in result.papers
    ]

    for key_target in benchmark.key_paper_dois_or_titles:
        clean_target = key_target.strip().lower()
        is_doi = clean_target.startswith("10.") or "doi.org" in clean_target
        target_doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", clean_target)

        matched = False
        if is_doi and target_doi in retrieved_dois:
            matched = True
        else:
            norm_target = re.sub(r"[^\w\s]", "", clean_target)
            for rt in retrieved_titles:
                if norm_target in rt or rt in norm_target:
                    matched = True
                    break
                if difflib.SequenceMatcher(None, norm_target, rt).ratio() >= 0.85:
                    matched = True
                    break

        if matched:
            found_papers.append(key_target)
        else:
            missed_papers.append(key_target)

    paper_recall = len(found_papers) / max(1, len(benchmark.key_paper_dois_or_titles))

    # 2. Topic Coverage
    agent_theme_text = " ".join([
        f"{t.title} {t.description}" for t in result.themes
    ]).lower()

    covered_topics = []
    missed_topics = []
    for topic in benchmark.expected_topics:
        topic_words = set(re.findall(r"\w+", topic.lower()))
        overlap = sum(1 for w in topic_words if w in agent_theme_text)
        if overlap >= max(1, len(topic_words) // 2):
            covered_topics.append(topic)
        else:
            missed_topics.append(topic)

    topic_overlap = len(covered_topics) / max(1, len(benchmark.expected_topics))

    # 3. Finding Alignment
    agent_text_parts: list[str] = []
    if result.synthesis:
        agent_text_parts.extend(result.synthesis.agreements)
        if result.synthesis.narrative_summary:
            agent_text_parts.append(result.synthesis.narrative_summary)
        for theme in result.synthesis.themes:
            agent_text_parts.extend(theme.key_findings)

    agent_synthesis_text = " ".join(agent_text_parts).lower()

    aligned_count = 0
    for finding in benchmark.ground_truth_findings:
        finding_words = set(re.findall(r"\w+", finding.lower()))
        match_count = sum(1 for w in finding_words if w in agent_synthesis_text)
        if match_count >= max(2, len(finding_words) // 3):
            aligned_count += 1

    alignment_score = aligned_count / max(1, len(benchmark.ground_truth_findings)) if benchmark.ground_truth_findings else 1.0

    summary = (
        f"Benchmark Comparison: Paper Recall: {paper_recall:.1%} ({len(found_papers)}/{len(benchmark.key_paper_dois_or_titles)}), "
        f"Topic Overlap: {topic_overlap:.1%} ({len(covered_topics)}/{len(benchmark.expected_topics)}), "
        f"Finding Alignment: {alignment_score:.1%}."
    )

    return BenchmarkComparisonResult(
        paper_recall=round(paper_recall, 3),
        found_key_papers=found_papers,
        missed_key_papers=missed_papers,
        topic_overlap_score=round(topic_overlap, 3),
        covered_topics=covered_topics,
        missed_topics=missed_topics,
        finding_alignment_score=round(alignment_score, 3),
        summary=summary
    )
