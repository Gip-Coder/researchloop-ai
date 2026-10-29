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
    evidence_level: str = Field(default="abstract_only", description="Evidence inspected: abstract_only or full_text")
    source_url: str | None = Field(default=None, description="URL or DOI supplied by the source record")
    supporting_evidence: list[str] = Field(default_factory=list, description="Verbatim source passages supporting this analysis")


class PaperEvidence(BaseModel):
    """Internal paper-to-theme matrix; unavailable evidence remains explicitly unknown."""

    paper_id: str
    title: str
    year: int | None = None
    source_url: str | None = None
    healthcare_relevance: str | None = None
    privacy_mechanism: str | None = None
    accuracy_evaluation: str | None = None
    security_threat_or_defense: str | None = None
    deployment_context: str | None = None
    dataset_and_method: str | None = None
    main_supported_finding: str | None = None
    author_reported_limitations: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    included_in_synthesis: bool = True
    evidence_level: str = "abstract_only"
    evidence_text: str | None = None


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
    evidence_matrix: list[PaperEvidence] = Field(default_factory=list, description="Paper-to-theme evidence matrix")
    quality_warnings: list[str] = Field(default_factory=list, description="Evidence limitations and unsupported areas")

