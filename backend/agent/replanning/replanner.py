"""
Replanning Agent for researchloop-ai.
Synthesizes critic reflection into updated, gap-targeted search plans.
"""

from __future__ import annotations

import logging
from backend.agent.models.search import SearchPlan
from backend.agent.models.research import ResearchState
from backend.agent.prompts.replanner import REPLANNER_SYSTEM_PROMPT, build_replanner_prompt
from backend.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class ReplanningAgent:
    """Agent responsible for iterative search plan adaptation driven by gap analysis."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def replan(self, state: ResearchState) -> SearchPlan:
        """
        Generate a revised SearchPlan targeting gaps identified by the Critic.
        Ensures new queries avoid duplicating prior queries.
        """
        if not state.search_plan or not state.reflection:
            raise ValueError("Cannot replan without an existing search_plan and reflection.")

        # Aggregate all previously executed queries to enforce novelty
        prior_queries = []
        for it in state.iteration_history:
            prior_queries.extend(it.queries_executed)
        if not prior_queries and state.search_plan:
            prior_queries.extend(state.search_plan.search_queries)

        prompt = build_replanner_prompt(
            research_question=state.research_question,
            previous_plan=state.search_plan,
            prior_queries=list(set(prior_queries)),
            reflection=state.reflection
        )

        try:
            new_plan = await self.llm.generate_structured(
                prompt=prompt,
                response_model=SearchPlan,
                system_prompt=REPLANNER_SYSTEM_PROMPT,
                max_retries=2
            )
            # Filter out queries that duplicate prior queries
            existing_set = {q.strip().lower() for q in prior_queries}
            non_duplicate_queries = [q for q in new_plan.search_queries if q.strip().lower() not in existing_set]

            if non_duplicate_queries:
                new_plan.search_queries = non_duplicate_queries
            elif state.reflection.recommended_queries:
                new_plan.search_queries = [
                    q for q in state.reflection.recommended_queries if q.strip().lower() not in existing_set
                ] or state.reflection.recommended_queries

            return new_plan

        except Exception as err:
            logger.error(f"[ReplanningAgent] Replanning failed: {err}. Building fallback revised plan.")
            return self._build_fallback_replan(state, prior_queries)

    def _build_fallback_replan(
        self,
        state: ResearchState,
        prior_queries: list[str]
    ) -> SearchPlan:
        reflection = state.reflection
        existing_set = {q.strip().lower() for q in prior_queries}

        # Build new queries directly from critic's recommendations and missing topics
        candidate_queries = []
        if reflection:
            for rec in reflection.recommended_queries:
                if rec.strip().lower() not in existing_set:
                    candidate_queries.append(rec)
            for miss in reflection.missing_topics:
                q = f"{state.research_question} {miss}"
                if q.strip().lower() not in existing_set:
                    candidate_queries.append(q)

        if not candidate_queries:
            candidate_queries = [
                f"{state.research_question} advanced analysis iteration {state.iteration + 1}",
                f"{state.research_question} empirical benchmarks"
            ]

        prev = state.search_plan
        return SearchPlan(
            research_question=state.research_question,
            sub_questions=reflection.missing_topics if (reflection and reflection.missing_topics) else (prev.sub_questions if prev else []),
            keywords=prev.keywords if prev else [],
            search_queries=candidate_queries[:6],
            preferred_sources=prev.preferred_sources if prev else ["arxiv", "semantic_scholar", "crossref"],
            date_range=prev.date_range if prev else None,
            inclusion_criteria=prev.inclusion_criteria if prev else [],
            exclusion_criteria=prev.exclusion_criteria if prev else []
        )

