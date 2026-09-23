"""
arXiv Academic Provider adapter using arXiv Atom API.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any
import httpx

from backend.agent.retrieval.base import AcademicSource
from backend.agent.models.paper import Paper

logger = logging.getLogger(__name__)

# Atom and arXiv XML namespaces
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom"
}


class ArxivProvider(AcademicSource):
    """Retrieval adapter for the official arXiv query API."""

    def __init__(
        self,
        timeout: float = 15.0,
        max_retries: int = 3
    ):
        super().__init__(name="arxiv", timeout=timeout, max_retries=max_retries)
        self.endpoint = "http://export.arxiv.org/api/query"

    async def search(
        self,
        query: str,
        limit: int = 10,
        start_year: int | None = None,
        end_year: int | None = None,
        **kwargs: Any
    ) -> list[Paper]:
        clean_query = re.sub(r"[^\w\s-]", " ", query).strip()
        search_query = f"all:{clean_query}"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        async def _call() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await client.get(self.endpoint, params=params)

        response = await self._execute_with_retry(_call)
        return self._parse_feed(response.text, start_year=start_year, end_year=end_year)

    def _parse_feed(
        self,
        xml_text: str,
        start_year: int | None = None,
        end_year: int | None = None
    ) -> list[Paper]:
        papers: list[Paper] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as err:
            logger.warning(f"[arxiv] XML parse error: {err}")
            return papers

        entries = root.findall("atom:entry", NAMESPACES)
        for entry in entries:
            title_elem = entry.find("atom:title", NAMESPACES)
            if title_elem is None or not title_elem.text:
                continue
            title = re.sub(r"\s+", " ", title_elem.text.strip())

            # Abstract / summary
            summary_elem = entry.find("atom:summary", NAMESPACES)
            abstract = re.sub(r"\s+", " ", summary_elem.text.strip()) if summary_elem is not None and summary_elem.text else None

            # Authors
            authors = []
            for author_node in entry.findall("atom:author", NAMESPACES):
                name_elem = author_node.find("atom:name", NAMESPACES)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # ID and URL
            id_elem = entry.find("atom:id", NAMESPACES)
            arxiv_url = id_elem.text.strip() if id_elem is not None and id_elem.text else None
            arxiv_id = arxiv_url.split("/abs/")[-1] if arxiv_url and "/abs/" in arxiv_url else (arxiv_url or "")

            # Publication year
            published_elem = entry.find("atom:published", NAMESPACES)
            pub_date = published_elem.text.strip() if published_elem is not None and published_elem.text else None
            year = int(pub_date[:4]) if pub_date and len(pub_date) >= 4 and pub_date[:4].isdigit() else None

            if start_year and year and year < start_year:
                continue
            if end_year and year and year > end_year:
                continue

            # DOI
            doi_elem = entry.find("arxiv:doi", NAMESPACES)
            doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

            # Categories
            categories = []
            for cat in entry.findall("atom:category", NAMESPACES):
                term = cat.attrib.get("term")
                if term:
                    categories.append(term)

            paper = Paper(
                id=f"arxiv-{arxiv_id.replace('/', '_')}",
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                venue="arXiv preprint",
                doi=doi,
                url=arxiv_url,
                source="arxiv",
                citation_count=0,
                publication_date=pub_date,
                external_ids={"arxiv": arxiv_id} if arxiv_id else {},
                categories=categories,
                raw_source_id=arxiv_id
            )
            papers.append(paper)

        return papers

