"""
Reflection and critic evaluation models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Reflection(BaseModel):
    """Structured critical evaluation produced by the Critic / Self-Reflection Agent."""

    coverage_score: float = Field(
        ge=0.0, le=1.0,
        description="Assessed coverage score of the research question (0.0 to 1.0)"
    )
    relevance_score: float = Field(
        ge=0.0, le=1.0,
        description="Assessed relevance score of the retrieved corpus (0.0 to 1.0)"
    )
    missing_topics: list[str] = Field(
        default_factory=list,
        description="Critical dimensions or sub-questions not adequately addressed"
    )
    weak_areas: list[str] = Field(
        default_factory=list,
        description="Aspects with shallow evidence or insufficient paper support"
    )
    contradictions: list[str] = Field(
        default_factory=list,
        description="Unresolved conflicting evidence in the retrieved literature"
    )
    outdated_areas: list[str] = Field(
        default_factory=list,
        description="Sub-topics where more recent work (past 1-2 years) is required"
    )
    recommended_queries: list[str] = Field(
        default_factory=list,
        description="Targeted search queries recommended to address gaps"
    )
    should_replan: bool = Field(
        default=True,
        description="Whether another iteration of retrieval and synthesis is warranted"
    )
    reason: str = Field(
        description="Clear rationale explaining the critic's assessment and decision"
    )
    evaluation_type: str = Field(
        default="llm_critic",
        description="Marks that this evaluation is LLM-based rather than heuristic"
    )
