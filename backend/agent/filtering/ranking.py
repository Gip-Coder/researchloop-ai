"""
Academic paper ranking and citation-count preference module.
Implements the 2019+ publication-year constraint and 10-15 citation preference policy.
"""

from __future__ import annotations

import logging
from typing import Sequence
from backend.agent.models.paper import Paper

logger = logging.getLogger(__name__)


def is_in_citation_range(paper: Paper, min_c: int = 10, max_c: int = 15) -> bool:
    """Check if paper has a verified citation count falling within [min_c, max_c]."""
    if paper.citation_count is None:
        return False
    return min_c <= paper.citation_count <= max_c


def rank_papers_for_synthesis(
    papers: Sequence[Paper],
    preferred_min_citations: int = 10,
    preferred_max_citations: int = 15,
    strict_citation_filtering: bool = False,
    min_year: int | None = None,
    allow_foundational: bool = False,
    min_citations: int = 0,
    allow_unknown_citations: bool = True,
) -> tuple[list[Paper], list[Paper]]:
    """
    Rank and partition papers for thematic synthesis based on relevance and citation preference.

    Policy:
    1. Year verification:
       - Papers published >= min_year (e.g. 2019) are eligible.
       - Papers with missing/unresolvable publication year are excluded from substantive review.
       - Papers published < min_year are excluded by default, UNLESS allow_foundational is True
         AND the paper was explicitly flagged as a foundational exception (is_foundational_exception=True).
    2. Citation Preference (10-15 range):
       - If strict_citation_filtering is True:
         Only papers with known citations in [preferred_min_citations, preferred_max_citations] are eligible.
       - If strict_citation_filtering is False (default):
         All relevant papers meeting year criteria remain eligible.
         Citation counts guide ranking priority:
           Tier 1: Verified in-range citations (10 <= citations <= 15).
           Tier 2: High-relevance papers (relevance_score >= 0.85) outside range or unknown.
           Tier 3: Other relevant papers with known citations (< 10 or > 15).
           Tier 4: Other relevant papers with unknown citations.
         Within tiers, papers are ordered by relevance_score descending, then proximity to [10, 15].

    Returns:
        (eligible_ranked_papers, excluded_papers)
    """
    eligible: list[Paper] = []
    excluded: list[Paper] = []

    for paper in papers:
        # Check year eligibility only if min_year is specified
        if min_year is not None:
            if paper.year is None:
                excluded.append(paper)
                continue

            if paper.year < min_year:
                if allow_foundational and paper.is_foundational_exception:
                    # Valid foundational exception
                    pass
                else:
                    excluded.append(paper)
                    continue

        # Check minimum citations constraint
        if min_citations is not None and min_citations > 0:
            if paper.citation_count is not None and paper.citation_count < min_citations:
                excluded.append(paper)
                continue
            if paper.citation_count is None and not allow_unknown_citations:
                excluded.append(paper)
                continue

        # Check strict citation filtering if enabled
        if strict_citation_filtering:
            if not is_in_citation_range(paper, preferred_min_citations, preferred_max_citations):
                excluded.append(paper)
                continue

        eligible.append(paper)

    def _citation_distance(c: int | None) -> float:
        if c is None:
            return 999.0
        if c < preferred_min_citations:
            return float(preferred_min_citations - c)
        if c > preferred_max_citations:
            return float(c - preferred_max_citations)
        return 0.0

    def _sort_key(p: Paper) -> tuple[int, float, float]:
        rel = p.relevance_score if p.relevance_score is not None else 0.5
        in_range = is_in_citation_range(p, preferred_min_citations, preferred_max_citations)

        if in_range:
            tier = 1
        elif rel >= 0.85:
            tier = 2
        elif p.citation_count is not None:
            tier = 3
        else:
            tier = 4

        # Within tier: higher relevance first (-rel), then closest citation distance
        return (tier, -rel, _citation_distance(p.citation_count))

    eligible.sort(key=_sort_key)
    return eligible, excluded
