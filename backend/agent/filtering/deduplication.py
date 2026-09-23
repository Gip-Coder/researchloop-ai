"""
Academic paper deduplication module with multi-tier matching and metadata merging.
"""

from __future__ import annotations

import difflib
import re
from typing import Sequence
from backend.agent.models.paper import Paper


class Deduplicator:
    """Multi-tier paper deduplicator prioritizing DOI, normalized title, and cautious fuzzy matching."""

    def __init__(self, fuzzy_threshold: float = 0.92):
        self.fuzzy_threshold = fuzzy_threshold

    def deduplicate(
        self,
        new_papers: Sequence[Paper],
        existing_papers: Sequence[Paper] | None = None
    ) -> list[Paper]:
        """
        Deduplicate papers against an existing corpus and among themselves.
        Returns the consolidated list with merged metadata.
        """
        consolidated: list[Paper] = [p.model_copy(deep=True) for p in (existing_papers or [])]

        for candidate in new_papers:
            match_index = self._find_duplicate_index(candidate, consolidated)
            if match_index is not None:
                # Merge metadata into existing record
                consolidated[match_index] = self._merge_papers(consolidated[match_index], candidate)
            else:
                consolidated.append(candidate.model_copy(deep=True))

        return consolidated

    def _find_duplicate_index(self, candidate: Paper, corpus: list[Paper]) -> int | None:
        cand_doi = self._normalize_doi(candidate.doi)
        cand_norm_title = self._normalize_title(candidate.title)

        for i, existing in enumerate(corpus):
            # 1. Exact DOI match
            exist_doi = self._normalize_doi(existing.doi)
            if cand_doi and exist_doi and cand_doi == exist_doi:
                return i

            # 2. Normalized Title match
            exist_norm_title = self._normalize_title(existing.title)
            if cand_norm_title and exist_norm_title and cand_norm_title == exist_norm_title:
                return i

            # 3. Cautious Fuzzy Title match
            if cand_norm_title and exist_norm_title:
                ratio = difflib.SequenceMatcher(None, cand_norm_title, exist_norm_title).ratio()
                if ratio >= self.fuzzy_threshold:
                    # Guard against false positives: check publication year or author overlap if available
                    if self._verify_fuzzy_match(candidate, existing):
                        return i

        return None

    def _verify_fuzzy_match(self, p1: Paper, p2: Paper) -> bool:
        """Verify fuzzy match with secondary metadata to avoid false positives."""
        # If both have years and they differ by more than 1 year, reject fuzzy match
        if p1.year and p2.year and abs(p1.year - p2.year) > 1:
            return False

        # If both have authors, check if at least one author surname overlaps
        if p1.authors and p2.authors:
            surnames1 = {a.split()[-1].lower() for a in p1.authors if a.strip()}
            surnames2 = {a.split()[-1].lower() for a in p2.authors if a.strip()}
            if surnames1 and surnames2 and not (surnames1 & surnames2):
                return False

        return True

    def _normalize_doi(self, doi: str | None) -> str | None:
        if not doi:
            return None
        clean = doi.strip().lower()
        clean = re.sub(r"^https?://(dx\.)?doi\.org/", "", clean)
        clean = re.sub(r"^doi:\s*", "", clean)
        return clean.strip() or None

    def _normalize_title(self, title: str | None) -> str:
        if not title:
            return ""
        clean = title.lower()
        clean = re.sub(r"[^\w\s]", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _merge_papers(self, target: Paper, source: Paper) -> Paper:
        """Merge the richest metadata between two representations of the same paper."""
        merged = target.model_copy(deep=True)

        # Prefer non-empty abstract or longer abstract
        if not merged.abstract and source.abstract:
            merged.abstract = source.abstract
        elif merged.abstract and source.abstract and len(source.abstract) > len(merged.abstract):
            merged.abstract = source.abstract

        # Prefer higher citation count
        merged.citation_count = max(merged.citation_count or 0, source.citation_count or 0)

        # Fill missing DOI
        if not merged.doi and source.doi:
            merged.doi = source.doi

        # Fill missing URL
        if not merged.url and source.url:
            merged.url = source.url

        # Fill missing year
        if not merged.year and source.year:
            merged.year = source.year

        # Fill missing venue
        if not merged.venue and source.venue:
            merged.venue = source.venue

        # Merge authors (prefer longer list)
        if len(source.authors) > len(merged.authors):
            merged.authors = list(source.authors)

        # Merge external IDs
        merged.external_ids = {**merged.external_ids, **source.external_ids}

        # Merge categories
        merged.categories = list(set(merged.categories + source.categories))

        return merged

