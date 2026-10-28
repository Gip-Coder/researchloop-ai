"""
Crossref Academic Provider adapter using Crossref REST API.
"""

from __future__ import annotations

import logging
import re
from typing import Any
import httpx

from backend.agent.retrieval.base import AcademicSource
from backend.agent.models.paper import Paper
from backend.agent.core.config import get_settings

logger = logging.getLogger(__name__)


class CrossrefProvider(AcademicSource):
    """Retrieval adapter for the official Crossref REST API."""

    def __init__(
        self,
        mailto: str | None = None,
        timeout: float = 15.0,
        max_retries: int = 3
    ):
        super().__init__(name="crossref", timeout=timeout, max_retries=max_retries)
        settings = get_settings()
        self.mailto = mailto or settings.crossref_mailto
        self.endpoint = "https://api.crossref.org/works"

    async def search(
        self,
        query: str,
        limit: int = 10,
        start_year: int | None = None,
        end_year: int | None = None,
        **kwargs: Any
    ) -> list[Paper]:
        params: dict[str, Any] = {
            "query": query,
            "rows": limit,
            "sort": "relevance",
            "order": "desc"
        }
        filter_parts = []
        if start_year:
            filter_parts.append(f"from-pub-date:{start_year}-01-01")
        if end_year:
            filter_parts.append(f"until-pub-date:{end_year}-12-31")
        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        headers = {
            "User-Agent": f"researchloop-ai/1.0 (mailto:{self.mailto})"
        }

        async def _call() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                return await client.get(self.endpoint, params=params, headers=headers)

        response = await self._execute_with_retry(_call)
        data = response.json()
        items = data.get("message", {}).get("items", [])

        papers: list[Paper] = []
        for item in items:
            normalized = self._normalize_paper(item, start_year=start_year, end_year=end_year)
            if normalized:
                papers.append(normalized)
        return papers

    def _normalize_paper(
        self,
        raw: dict[str, Any],
        start_year: int | None = None,
        end_year: int | None = None
    ) -> Paper | None:
        titles = raw.get("title", [])
        title = titles[0].strip() if titles else ""
        if not title:
            return None

        # Authors
        authors = []
        for a in raw.get("author", []):
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            name = f"{given} {family}".strip() or a.get("name", "").strip()
            if name:
                authors.append(name)

        # Abstract (often contains JATS XML like <jats:p>...</jats:p>)
        raw_abstract = raw.get("abstract")
        clean_abstract = None
        if raw_abstract:
            clean_abstract = re.sub(r"<[^>]+>", " ", raw_abstract)
            clean_abstract = re.sub(r"\s+", " ", clean_abstract).strip()

        # Authoritative publication year & date normalization
        year, pub_date = self._extract_year_and_date(raw)

        if start_year and year and year < start_year:
            return None
        if end_year and year and year > end_year:
            return None

        # Venue / Container Title
        container = raw.get("container-title", [])
        venue = container[0].strip() if container else None

        doi = raw.get("DOI")
        url = raw.get("URL") or (f"https://doi.org/{doi}" if doi else None)

        # Crossref citation count: is-referenced-by-count
        ref_count = raw.get("is-referenced-by-count")
        citation_count: int | None = None
        citation_count_available: bool = False
        if ref_count is not None and isinstance(ref_count, (int, float)):
            citation_count = int(ref_count)
            citation_count_available = True

        return Paper(
            id=f"crossref-{doi.replace('/', '_')}" if doi else f"crossref-{abs(hash(title))}",
            title=title,
            authors=authors,
            abstract=clean_abstract,
            year=year,
            venue=venue,
            doi=doi,
            url=url,
            source="crossref",
            citation_count=citation_count,
            citation_count_available=citation_count_available,
            publication_date=pub_date,
            external_ids={"doi": doi} if doi else {},
            categories=raw.get("subject", []),
            raw_source_id=doi
        )

    def _extract_year_and_date(self, raw: dict[str, Any]) -> tuple[int | None, str | None]:
        """
        Normalize publication year and date across print, online, and issued date-parts.
        Prefers formal issued date, with fallback to earliest verified publication date.
        """
        date_candidates: list[tuple[int, str, str]] = []
        for field in ("issued", "published-print", "published-online", "published", "created"):
            obj = raw.get(field)
            if obj and isinstance(obj, dict) and "date-parts" in obj:
                parts = obj.get("date-parts", [])
                if parts and parts[0] and isinstance(parts[0][0], int):
                    y = parts[0][0]
                    m = parts[0][1] if len(parts[0]) > 1 and isinstance(parts[0][1], int) else 1
                    d = parts[0][2] if len(parts[0]) > 2 and isinstance(parts[0][2], int) else 1
                    date_str = f"{y:04d}-{m:02d}-{d:02d}"
                    date_candidates.append((y, date_str, field))

        if not date_candidates:
            return None, None

        # If issued exists, it is the canonical bibliographic record
        for y, d_str, fld in date_candidates:
            if fld == "issued":
                return y, d_str

        # Otherwise take the earliest publication date
        date_candidates.sort(key=lambda c: c[0])
        return date_candidates[0][0], date_candidates[0][1]
