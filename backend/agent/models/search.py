"""
Search and planning models for academic query generation and execution.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from backend.agent.core.config import get_settings
from backend.agent.models.common import DateRange


class SearchQuery(BaseModel):
    """Structured search query targeting specific sub-dimensions."""

    query: str = Field(description="Search terms for academic API")
    target_dimension: str = Field(default="", description="Research sub-question or concept targeted")
    source: str | None = Field(default=None, description="Preferred provider for this query if specific")


class SearchPlan(BaseModel):
    """Structured output of the Planning and Replanning agents."""

    research_question: str = Field(description="The primary research question")
    sub_questions: list[str] = Field(default_factory=list, description="Decomposed sub-questions")
    keywords: list[str] = Field(default_factory=list, description="Extracted academic keywords and concepts")
    search_queries: list[str] = Field(default_factory=list, description="Actionable search queries for retrieval")
    preferred_sources: list[str] = Field(
        default_factory=lambda: list(get_settings().preferred_sources),
        description="Target academic sources (defaults to arxiv, crossref)"
    )
    date_range: DateRange | None = Field(
        default=None,
        description="Deprecated; publication year does not restrict retrieval"
    )
    min_publication_year: int | None = Field(
        default=None,
        description="Deprecated; publication year does not restrict eligibility"
    )
    min_citations: int = Field(
        default_factory=lambda: get_settings().default_min_citations,
        description="Minimum citation count constraint (default 5)"
    )
    allow_unknown_citations: bool = Field(
        default_factory=lambda: get_settings().default_allow_unknown_citations,
        description="Allow papers with unknown citations (e.g. arXiv preprints)"
    )
    allow_foundational_exceptions: bool = Field(
        default_factory=lambda: get_settings().default_allow_foundational_exceptions,
        description="Whether pre-2019 foundational literature exceptions are allowed"
    )
    inclusion_criteria: list[str] = Field(default_factory=list, description="Criteria for keeping retrieved papers")
    exclusion_criteria: list[str] = Field(default_factory=list, description="Criteria for discarding retrieved papers")
