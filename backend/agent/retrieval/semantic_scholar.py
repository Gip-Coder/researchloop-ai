"""
Semantic Scholar Academic Provider adapter.
"""

from __future__ import annotations

import logging
from typing import Any
import httpx

from backend.agent.retrieval.base import AcademicSource
from backend.agent.models.paper import Paper
from backend.agent.core.config import get_settings

logger = logging.getLogger(__name__)


class SemanticScholarProvider(AcademicSource):
    """Retrieval adapter for the Semantic Scholar Graph API."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 15.0,
        max_retries: int = 3
    ):
        super().__init__(name="semantic_scholar", timeout=timeout, max_retries=max_retries)
        settings = get_settings()
        self.api_key = api_key or settings.semantic_scholar_api_key
        self.endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(
        self,
        query: str,
        limit: int = 10,
        start_year: int | None = None,
        end_year: int | None = None,
        **kwargs: Any
    ) -> list[Paper]:
        fields = "paperId,title,authors,abstract,year,venue,citationCount,externalIds,url,publicationDate,fieldsOfStudy"
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "fields": fields
        }
        if start_year or end_year:
            s_year = start_year or 1990
            e_year = end_year or 2030
            params["year"] = f"{s_year}-{e_year}"

        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        async def _call() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await client.get(self.endpoint, params=params, headers=headers)

        response = await self._execute_with_retry(_call)
        data = response.json()
        raw_items = data.get("data", [])

        papers: list[Paper] = []
        for item in raw_items:
            normalized = self._normalize_paper(item)
            if normalized:
                papers.append(normalized)
        return papers

    def _normalize_paper(self, raw: dict[str, Any]) -> Paper | None:
        title = (raw.get("title") or "").strip()
        if not title:
            return None

        paper_id = raw.get("paperId") or ""
        authors = [a.get("name", "") for a in raw.get("authors", []) if a.get("name")]
        abstract = raw.get("abstract")
        year = raw.get("year")
        venue = raw.get("venue")
        citation_count = raw.get("citationCount") or 0

        ext_ids = raw.get("externalIds") or {}
        doi = ext_ids.get("DOI")
        arxiv_id = ext_ids.get("ArXiv")
        url = raw.get("url") or (f"https://doi.org/{doi}" if doi else (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None))
        categories = raw.get("fieldsOfStudy") or []

        return Paper(
            id=f"s2-{paper_id}" if paper_id else f"s2-{abs(hash(title))}",
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            venue=venue,
            doi=doi,
            url=url,
            source="semantic_scholar",
            citation_count=citation_count,
            publication_date=raw.get("publicationDate"),
            external_ids={k: str(v) for k, v in ext_ids.items() if v},
            categories=categories,
            raw_source_id=paper_id
        )
