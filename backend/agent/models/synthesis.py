"""
Synthesis models capturing per-paper analysis, thematic groupings, and cross-paper insights.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaperAnalysis(BaseModel):
    """Deep academic extraction for an individual relevant paper."""

    paper_id: str = Field(description="Canonical ID of the analyzed paper")
    title: str = Field(description="Title of the paper")
    research_problem: str = Field(description="Core scientific problem or objective addressed")
    methodology: str = Field(description="Methodological approach, architecture, or theoretical framework")
    dataset: str | None = Field(default=None, description="Benchmarks, datasets, or experimental corpus used")
    key_findings: list[str] = Field(default_factory=list, description="Primary empirical or theoretical results")
    contribution: str = Field(description="Novel contribution to the research field")
    limitations: list[str] = Field(default_factory=list, description="Reported or identified limitations and caveats")
    relevance: str = Field(description="Specific relevance to the overarching research question")


class Theme(BaseModel):
    """Thematic cluster dynamically discovered across multiple papers."""

    id: str = Field(description="Identifier for the theme (e.g. 'theme-1')")
    title: str = Field(description="Descriptive title of the thematic cluster")
    description: str = Field(description="Narrative explanation of the theme")
    paper_ids: list[str] = Field(default_factory=list, description="IDs of papers contributing to this theme")
    key_findings: list[str] = Field(default_factory=list, description="Consolidated findings within this theme")
    contradictions_or_tensions: list[str] = Field(
        default_factory=list,
        description="Conflicting results or tensions observed across papers in this theme"
    )


class CrossPaperInsight(BaseModel):
    """Comparative analysis across papers."""

    category: str = Field(description="Category: 'agreement', 'difference', 'contradiction', 'methodology', 'gap'")
    summary: str = Field(description="Synthesized observation")
    involved_paper_ids: list[str] = Field(default_factory=list, description="Referenced papers")


class Synthesis(BaseModel):
    """Comprehensive literature synthesis produced by the Synthesis Agent."""

    paper_analyses: list[PaperAnalysis] = Field(default_factory=list, description="Per-paper extractions")
    themes: list[Theme] = Field(default_factory=list, description="Dynamically generated thematic clusters")
    agreements: list[str] = Field(default_factory=list, description="Areas of consensus across literature")
    differences: list[str] = Field(default_factory=list, description="Diverging findings or perspectives")
    contradictions: list[str] = Field(default_factory=list, description="Directly contradictory empirical claims")
    methodological_differences: list[str] = Field(default_factory=list, description="Contrasting methodologies")
    trends: list[str] = Field(default_factory=list, description="Emerging patterns and research trajectories")
    research_gaps: list[str] = Field(default_factory=list, description="Unexplored questions and open challenges")
    narrative_summary: str = Field(default="", description="Executive narrative synthesis of the state-of-the-art")
