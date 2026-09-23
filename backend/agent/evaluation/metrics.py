"""
Quantitative research-level evaluation metrics.
Provides functions for coverage, relevance, recall, citation distribution, and coherence.
"""

from __future__ import annotations

import difflib
import statistics
from typing import Sequence, Any

from backend.agent.models.paper import Paper
from backend.agent.models.synthesis import Synthesis, Theme
from backend.agent.models.research import ResearchState


def compute_coverage(state: ResearchState) -> float:
    """
    Compute coverage score for the current research state.
    Uses the Critic's evaluated coverage_score if available;
    otherwise computes heuristic based on sub-question representation and paper volume.
    """
    if state.reflection and state.reflection.coverage_score > 0:
        return state.reflection.coverage_score

    if not state.relevant_papers:
        return 0.0

    # Fallback heuristic: paper volume + sub-question coverage
    sub_q_count = len(state.search_plan.sub_questions) if state.search_plan else 3
    papers_per_subq = len(state.relevant_papers) / max(1, sub_q_count)
    score = min(1.0, papers_per_subq * 0.25)
    return round(score, 3)


def compute_relevance(papers: Sequence[Paper]) -> float:
    """
    Compute average relevance score across a collection of papers.
    Returns 0.0 if no papers or no relevance scores.
    """
    if not papers:
        return 0.0

    scores = [p.relevance_score for p in papers if p.relevance_score is not None]
    if not scores:
        # Default based on binary is_relevant
        relevant_count = sum(1 for p in papers if p.is_relevant)
        return round(relevant_count / len(papers), 3)

    return round(sum(scores) / len(scores), 3)


def compute_paper_recall(
    retrieved_papers: Sequence[Paper],
    ground_truth_identifiers: Sequence[str]
) -> float:
    """
    Compute recall of key papers against a ground-truth list of DOIs or titles.
    """
    if not ground_truth_identifiers:
        return 1.0

    retrieved_dois = {
        (p.doi or "").lower().strip() for p in retrieved_papers if p.doi
    }
    retrieved_titles = [
        p.title.lower().strip() for p in retrieved_papers
    ]

    matched = 0
    for target in ground_truth_identifiers:
        clean_target = target.lower().strip()
        is_doi = clean_target.startswith("10.") or "doi.org" in clean_target

        if is_doi and clean_target in retrieved_dois:
            matched += 1
        else:
            if any(
                clean_target in rt or rt in clean_target or difflib.SequenceMatcher(None, clean_target, rt).ratio() >= 0.85
                for rt in retrieved_titles
            ):
                matched += 1

    return round(matched / len(ground_truth_identifiers), 3)


def compute_topic_coverage(
    themes: Sequence[Theme],
    expected_topics: Sequence[str]
) -> float:
    """
    Compute the proportion of expected research topics represented in the themes.
    """
    if not expected_topics:
        return 1.0
    if not themes:
        return 0.0

    theme_text = " ".join([f"{t.title} {t.description}" for t in themes]).lower()
    covered = 0
    for topic in expected_topics:
        words = set(topic.lower().split())
        if any(w in theme_text for w in words):
            covered += 1

    return round(covered / len(expected_topics), 3)


def compute_citation_distribution(papers: Sequence[Paper]) -> dict[str, Any]:
    """
    Compute empirical citation distribution statistics across papers.
    """
    citations = [p.citation_count for p in papers if p.citation_count is not None]
    if not citations:
        return {
            "total_citations": 0,
            "mean_citations": 0.0,
            "median_citations": 0.0,
            "max_citations": 0,
            "papers_with_citation_data": 0
        }

    return {
        "total_citations": sum(citations),
        "mean_citations": round(statistics.mean(citations), 2),
        "median_citations": round(statistics.median(citations), 2),
        "max_citations": max(citations),
        "papers_with_citation_data": len(citations)
    }


def compute_coherence(synthesis: Synthesis | None) -> float:
    """
    Compute structural and dialectical coherence of a literature synthesis.

    Evaluates:
    1. Grounding: Are themes linked to valid analyzed paper IDs? (Weight: 25%)
    2. Substantive Breadth: Are themes supported by multiple papers with findings? (Weight: 25%)
    3. Dialectical Nuance: Does the synthesis document agreements, differences, and contradictions? (Weight: 25%)
    4. Completeness & Narrative: Presence of actionable research gaps and comprehensive narrative? (Weight: 25%)

    Returns a normalized coherence score between 0.0 and 1.0.
    """
    if synthesis is None:
        return 0.0

    analyzed_paper_ids = {a.paper_id for a in synthesis.paper_analyses}

    # 1. Theme-to-paper grounding
    if synthesis.themes and analyzed_paper_ids:
        grounded_links = 0
        total_links = 0
        for theme in synthesis.themes:
            for pid in theme.paper_ids:
                total_links += 1
                if pid in analyzed_paper_ids:
                    grounded_links += 1
        grounding_score = (grounded_links / max(1, total_links)) if total_links > 0 else 0.5
    else:
        grounding_score = 0.5 if synthesis.themes else 0.0

    # 2. Substantive theme depth
    if synthesis.themes:
        substantive_themes = sum(
            1 for t in synthesis.themes
            if len(t.paper_ids) >= 1 and len(t.key_findings) >= 1
        )
        theme_depth_score = substantive_themes / len(synthesis.themes)
    else:
        theme_depth_score = 0.0

    # 3. Dialectical nuance (balance between consensus and tension/contradiction)
    has_agreements = len(synthesis.agreements) > 0
    has_differences = len(synthesis.differences) > 0
    has_contradictions = len(synthesis.contradictions) > 0 or len(synthesis.methodological_differences) > 0

    nuance_points = sum([has_agreements, has_differences, has_contradictions])
    nuance_score = nuance_points / 3.0

    # 4. Actionable gaps and narrative summary
    has_gaps = len(synthesis.research_gaps) > 0
    has_narrative = len(synthesis.narrative_summary.strip()) >= 50
    narrative_score = (1.0 if (has_gaps and has_narrative) else (0.5 if (has_gaps or has_narrative) else 0.0))

    # Composite weighted coherence
    total_coherence = (
        0.25 * grounding_score
        + 0.25 * theme_depth_score
        + 0.25 * nuance_score
        + 0.25 * narrative_score
    )

    return round(min(1.0, max(0.0, total_coherence)), 3)
