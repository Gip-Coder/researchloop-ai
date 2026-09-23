"""
Critic / Self-Reflection Agent for researchloop-ai.
Evaluates research state completeness, identifies blind spots, and recommends query refinements.
"""

from __future__ import annotations

import logging
from backend.agent.models.reflection import Reflection
from backend.agent.models.research import ResearchState
from backend.agent.prompts.critic import CRITIC_SYSTEM_PROMPT, build_critic_prompt
from backend.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class CriticAgent:
    """Agent responsible for rigorous critical evaluation and gap detection."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def evaluate(self, state: ResearchState) -> Reflection:
        """
        Evaluate current synthesis against research question, plan, and literature corpus.
        Returns a structured Reflection object with coverage score and gap analysis.
        """
        prompt = build_critic_prompt(
            research_question=state.research_question,
            search_plan=state.search_plan,
            relevant_papers=state.relevant_papers,
            synthesis=state.synthesis,
            iteration=state.iteration
        )

        try:
            reflection = await self.llm.generate_structured(
                prompt=prompt,
                response_model=Reflection,
                system_prompt=CRITIC_SYSTEM_PROMPT,
                max_retries=2
            )
            return reflection

        except Exception as err:
            logger.error(f"[CriticAgent] Reflection evaluation failed: {err}. Building fallback reflection.")
            return self._build_fallback_reflection(state)

    def _build_fallback_reflection(self, state: ResearchState) -> Reflection:
        paper_count = len(state.relevant_papers)
        # Heuristic coverage estimate
        est_coverage = min(0.95, paper_count * 0.15)
        should_replan = (paper_count < 6) and (state.iteration < 3)

        return Reflection(
            coverage_score=round(est_coverage, 2),
            relevance_score=0.80 if paper_count > 0 else 0.0,
            missing_topics=["Empirical benchmarks and comparative evaluations"] if should_replan else [],
            weak_areas=["Long-tail edge cases"] if should_replan else [],
            contradictions=[],
            outdated_areas=[],
            recommended_queries=[
                f"{state.research_question} benchmark evaluation",
                f"{state.research_question} empirical comparison"
            ] if should_replan else [],
            should_replan=should_replan,
            reason=(
                f"Retrieved {paper_count} relevant papers across {state.iteration} iterations. "
                + ("Further retrieval recommended to expand coverage." if should_replan else "Adequate initial coverage achieved.")
            ),
            evaluation_type="heuristic_fallback"
        )

