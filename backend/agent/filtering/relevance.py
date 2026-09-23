"""
Relevance filtering module scoring candidate literature against research objectives.
"""

from __future__ import annotations

import asyncio
from typing import Sequence
from pydantic import BaseModel, Field

from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.agent.prompts.relevance import RELEVANCE_SYSTEM_PROMPT, build_relevance_prompt
from backend.providers.llm.base import LLMProvider


class RelevanceDecision(BaseModel):
    """Schema for individual paper relevance evaluation."""

    is_relevant: bool = Field(description="Whether the paper meets criteria")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Confidence/relevance score")
    relevance_reason: str = Field(description="Justification for inclusion or rejection")


class RelevanceFilter:
    """Evaluates retrieved papers against criteria using structured LLM reasoning and criteria checks."""

    def __init__(self, llm_provider: LLMProvider, threshold: float = 0.5):
        self.llm = llm_provider
        self.threshold = threshold

    async def filter_papers(
        self,
        papers: Sequence[Paper],
        plan: SearchPlan,
        max_concurrent: int = 5
    ) -> tuple[list[Paper], list[Paper]]:
        """
        Evaluate candidate papers.
        Returns (relevant_papers, rejected_papers).
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _eval_one(paper: Paper) -> Paper:
            # Check temporal criteria first
            if plan.date_range and paper.year:
                if plan.date_range.start_year and paper.year < plan.date_range.start_year:
                    p = paper.model_copy()
                    p.is_relevant = False
                    p.relevance_score = 0.1
                    p.relevance_reason = f"Published in {paper.year}, prior to start_year {plan.date_range.start_year}."
                    return p
                if plan.date_range.end_year and paper.year > plan.date_range.end_year:
                    p = paper.model_copy()
                    p.is_relevant = False
                    p.relevance_score = 0.1
                    p.relevance_reason = f"Published in {paper.year}, after end_year {plan.date_range.end_year}."
                    return p

            prompt = build_relevance_prompt(
                research_question=plan.research_question,
                inclusion_criteria=plan.inclusion_criteria,
                exclusion_criteria=plan.exclusion_criteria,
                paper_id=paper.id,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                year=paper.year
            )

            async with semaphore:
                try:
                    decision = await self.llm.generate_structured(
                        prompt=prompt,
                        response_model=RelevanceDecision,
                        system_prompt=RELEVANCE_SYSTEM_PROMPT
                    )
                    p = paper.model_copy()
                    p.is_relevant = decision.is_relevant and (decision.relevance_score >= self.threshold)
                    p.relevance_score = decision.relevance_score
                    p.relevance_reason = decision.relevance_reason
                    return p
                except Exception as err:
                    # Deterministic fallback on evaluation error: check keyword overlap
                    p = paper.model_copy()
                    text = f"{p.title} {p.abstract or ''}".lower()
                    kw_matches = sum(1 for kw in plan.keywords if kw.lower() in text)
                    score = min(1.0, kw_matches * 0.25)
                    p.is_relevant = score >= self.threshold
                    p.relevance_score = score
                    p.relevance_reason = f"Fallback keyword assessment ({kw_matches} keywords matched; LLM error: {err})"
                    return p

        tasks = [_eval_one(p) for p in papers]
        evaluated = await asyncio.gather(*tasks)

        relevant = [p for p in evaluated if p.is_relevant]
        rejected = [p for p in evaluated if not p.is_relevant]
        return relevant, rejected
