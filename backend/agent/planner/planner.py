"""
Planning Agent for researchloop-ai.
Deconstructs complex research questions into structured search plans.
"""

from __future__ import annotations

import logging
from backend.agent.core.config import get_settings
from backend.agent.models.common import DateRange
from backend.agent.models.search import SearchPlan
from backend.agent.prompts.planner import PLANNER_SYSTEM_PROMPT, build_planner_prompt
from backend.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class PlanningAgent:
    """Agent responsible for initial research question decomposition and search planning."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def plan(self, research_question: str) -> SearchPlan:
        """
        Deconstruct research question into structured search queries and criteria.
        Validates output against SearchPlan schema with automatic retry and graceful fallback.
        """
        prompt = build_planner_prompt(research_question)

        try:
            plan = await self.llm.generate_structured(
                prompt=prompt,
                response_model=SearchPlan,
                system_prompt=PLANNER_SYSTEM_PROMPT,
                max_retries=2
            )
            # Ensure preferred_sources respects configured defaults if omitted or empty
            settings = get_settings()
            if not plan.preferred_sources:
                plan.preferred_sources = list(settings.preferred_sources)
            return plan

        except Exception as err:
            logger.error(f"[PlanningAgent] Failed to generate structured plan: {err}. Building robust fallback plan.")
            return self._build_fallback_plan(research_question)

    def _build_fallback_plan(self, research_question: str) -> SearchPlan:
        """Generate a deterministic fallback search plan with phrase-based queries."""
        settings = get_settings()
        words = [w for w in research_question.split() if len(w) > 3]
        primary_keywords = words[:6]
        phrase = " ".join(words[:3]) if len(words) >= 3 else research_question

        # Construct meaningful academic phrases combining quoted concepts with modifiers
        queries = [
            f'"{phrase}" empirical evaluation',
            f'"{phrase}" benchmark factuality',
            f'"{phrase}" architectural analysis',
            f'"{phrase}" state of the art survey',
        ]

        return SearchPlan(
            research_question=research_question,
            sub_questions=[
                f"What are the foundational mechanisms of {research_question}?",
                f"What are the current empirical benchmarks and evaluation standards?",
                f"What are the primary limitations and open challenges?"
            ],
            keywords=primary_keywords,
            search_queries=queries,
            preferred_sources=list(settings.preferred_sources),
            min_publication_year=settings.default_min_publication_year,
            min_citations=settings.default_min_citations,
            allow_unknown_citations=settings.default_allow_unknown_citations,
            date_range=DateRange(start_year=settings.default_min_publication_year) if settings.default_min_publication_year else None,
            inclusion_criteria=[
                "Directly investigates the core research question",
                "Presents empirical or theoretical methodologies",
            ] + ([f"Published in {settings.default_min_publication_year} or later"] if settings.default_min_publication_year else [])
            + ([f"Minimum citation count: {settings.default_min_citations}"] if settings.default_min_citations else []),
            exclusion_criteria=[
                "Non-scholarly or superficial opinion articles",
                "Completely unrelated domain applications",
            ] + ([f"Published prior to {settings.default_min_publication_year} unless foundational"] if settings.default_min_publication_year else [])
            + ([f"Known citation count strictly below {settings.default_min_citations}"] if settings.default_min_citations else [])
        )
