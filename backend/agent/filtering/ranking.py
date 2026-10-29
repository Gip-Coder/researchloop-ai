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
    1. Publication year is descriptive metadata and never a selection criterion.
    2. Citation Preference (10-15 range):
       - If strict_citation_filtering is True:
         Only papers with known citations in [preferred_min_citations, preferred_max_citations] are eligible.
       - If strict_citation_filtering is False (default):
         All relevant papers remain eligible regardless of publication year.
         Citation counts guide ranking priority:
         Relevance is the primary rank. In-range counts break ties as a preference only;
         unknown counts remain unknown and are never treated as zero.

    Returns:
        (eligible_ranked_papers, excluded_papers)
    """
    eligible: list[Paper] = []
    excluded: list[Paper] = []

    for paper in papers:
        # Publication year does not affect eligibility. Keep min_year and
        # allow_foundational in the signature for compatibility with callers.

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

    def _sort_key(p: Paper) -> tuple[float, int, float]:
        rel = p.relevance_score if p.relevance_score is not None else 0.5
        in_range = is_in_citation_range(p, preferred_min_citations, preferred_max_citations)
        # Similar-relevance papers prefer the requested citation range; citation
        # metadata never outranks a more relevant paper.
        citation_preference = 0 if in_range else (1 if p.citation_count is not None else 2)
        return (-rel, citation_preference, _citation_distance(p.citation_count))

    eligible.sort(key=_sort_key)
    return eligible, excluded
