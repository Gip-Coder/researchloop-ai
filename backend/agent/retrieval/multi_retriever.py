"""
Multi-source academic retriever orchestrator with provider failure isolation and caching.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Awaitable, Any

from backend.agent.core.cache import QueryCache
from backend.agent.core.config import get_settings
from backend.agent.models.common import AgentEvent, EventType
from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.agent.retrieval.base import AcademicSource
from backend.agent.retrieval.mock_retriever import MockAcademicProvider
from backend.agent.retrieval.semantic_scholar import SemanticScholarProvider
from backend.agent.retrieval.arxiv import ArxivProvider
from backend.agent.retrieval.crossref import CrossrefProvider

logger = logging.getLogger(__name__)


class MultiProviderRetriever:
    """Orchestrates concurrent retrieval across academic sources with failure isolation."""

    def __init__(
        self,
        providers: list[AcademicSource] | None = None,
        mock_mode: bool = False,
        cache_enabled: bool = True
    ):
        settings = get_settings()
        self.mock_mode = mock_mode or settings.is_mock_mode
        self.cache = QueryCache(enabled=cache_enabled)

        if providers is not None:
            self.providers = {p.name: p for p in providers}
        else:
            configured_sources = set(settings.preferred_sources)
            self.providers = {}
            if "arxiv" in configured_sources:
                self.providers["arxiv"] = (
                    MockAcademicProvider(name="arxiv")
                    if self.mock_mode
                    else ArxivProvider(
                        timeout=settings.academic_request_timeout,
                        max_retries=settings.academic_max_retries,
                    )
                )
            if "crossref" in configured_sources:
                self.providers["crossref"] = (
                    MockAcademicProvider(name="crossref")
                    if self.mock_mode
                    else CrossrefProvider(
                        timeout=settings.academic_request_timeout,
                        max_retries=settings.academic_max_retries,
                    )
                )
            if "semantic_scholar" in configured_sources:
                self.providers["semantic_scholar"] = (
                    MockAcademicProvider(name="semantic_scholar")
                    if self.mock_mode
                    else SemanticScholarProvider(
                        timeout=settings.academic_request_timeout,
                        max_retries=settings.academic_max_retries,
                    )
                )

    async def retrieve_for_plan(
        self,
        plan: SearchPlan,
        iteration: int = 1,
        event_callback: Callable[[AgentEvent], Awaitable[None]] | None = None
    ) -> list[Paper]:
        """
        Execute all search queries in the plan across configured providers concurrently.
        Implements strict provider failure isolation. Excluded providers are never queried.
        """
        # Only query sources that are both requested by the plan and actively configured/instantiated
        target_sources = [s for s in plan.preferred_sources if s in self.providers]
        if not target_sources:
            target_sources = list(self.providers.keys())

        # If no providers are available at all
        if not target_sources:
            logger.warning("[MultiRetriever] No retrieval providers active in registry.")
            return []

        # Publication year is returned as metadata; it does not constrain retrieval.
        start_year = None
        end_year = None

        tasks = []
        task_descriptors = []

        for query in plan.search_queries:
            for source_name in target_sources:
                provider = self.providers[source_name]
                tasks.append(
                    self._cached_search(
                        provider=provider,
                        query=query,
                        start_year=start_year,
                        end_year=end_year
                    )
                )
                task_descriptors.append((source_name, query))

        # Run all provider tasks concurrently with return_exceptions=True for failure isolation
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_papers: list[Paper] = []
        for (source_name, query), outcome in zip(task_descriptors, results):
            if isinstance(outcome, Exception):
                logger.error(
                    f"[MultiRetriever] Source '{source_name}' failed for query '{query}': {outcome}"
                )
                if event_callback:
                    # Telemetry must never break provider failure isolation.
                    try:
                        await event_callback(
                            AgentEvent(
                                type=EventType.RETRIEVAL_FAILED.value,
                                iteration=iteration,
                                message=f"Provider '{source_name}' failed: {outcome}",
                                metadata={"source": source_name, "query": query, "error": str(outcome)}
                            )
                        )
                    except Exception as cb_err:
                        logger.warning(f"[MultiRetriever] Failure event callback raised: {cb_err}")
            else:
                for paper in outcome:
                    if query not in paper.matched_queries:
                        paper.matched_queries.append(query)
                all_papers.extend(outcome)

        return all_papers

    async def _cached_search(
        self,
        provider: AcademicSource,
        query: str,
        start_year: int | None,
        end_year: int | None
    ) -> list[Paper]:
        cache_key = {
            "source": provider.name,
            # Provider implementation is part of the key: mock providers reuse names,
            # so keeping provider_impl prevents cross-contamination.
            "provider_impl": f"{type(provider).__module__}.{type(provider).__qualname__}",
            "query": query,
            "start_year": start_year,
            "end_year": end_year
        }

        # Check cache
        cached = await self.cache.get("retrieval", cache_key)
        if cached is not None:
            return [Paper.model_validate(p) for p in cached]

        papers = await provider.search(
            query=query,
            limit=10,
            start_year=start_year,
            end_year=end_year
        )

        # Store in cache
        serializable = [p.model_dump() for p in papers]
        await self.cache.set("retrieval", cache_key, serializable)
        return papers
