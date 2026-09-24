"""
Canonical academic paper schema and normalization models.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class Paper(BaseModel):
    """Canonical representation of an academic paper normalized across all providers."""

    id: str = Field(description="Unique canonical identifier for the paper")
    title: str = Field(description="Title of the paper")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    abstract: str | None = Field(default=None, description="Abstract text if available")
    year: int | None = Field(default=None, description="Publication year")
    venue: str | None = Field(default=None, description="Conference, journal, or book venue")
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    url: str | None = Field(default=None, description="Canonical or landing URL")
    source: str = Field(description="Originating academic provider (e.g. 'arxiv', 'semantic_scholar', 'crossref')")
    citation_count: int | None = Field(default=0, description="Estimated citation count if reported")
    publication_date: str | None = Field(default=None, description="ISO-formatted publication date if known")
    external_ids: dict[str, str] = Field(default_factory=dict, description="Provider-specific IDs (e.g., arxiv, corpusId)")
    categories: list[str] = Field(default_factory=list, description="Subject categories or taxonomy tags")
    raw_source_id: str | None = Field(default=None, description="ID assigned by source provider")

    # Fields populated after relevance filtering stage
    is_relevant: bool | None = Field(default=None, description="Whether the paper passed relevance filtering")
    relevance_score: float | None = Field(default=None, description="Relevance score between 0.0 and 1.0")
    relevance_reason: str | None = Field(default=None, description="Rationale for retaining or rejecting paper")


class PaperRelevance(BaseModel):
    """Evaluation of an academic paper's relevance to the research inquiry."""

    paper_id: str = Field(description="Unique identifier of the evaluated paper")
    is_relevant: bool = Field(description="Whether the paper passed relevance filtering")
    relevance_score: float = Field(default=0.0, description="Relevance score between 0.0 and 1.0")
    relevance_reason: str = Field(default="", description="Rationale for retaining or rejecting paper")


