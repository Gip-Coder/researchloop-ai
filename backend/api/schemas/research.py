"""
Pydantic API DTO schemas for researchloop-ai web interface.
Provides clear separation between internal agent schemas and API response contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ResearchConfigInput(BaseModel):
    """User-configurable options for launching a research run."""
    max_iterations: int = Field(default=3, ge=1, le=10, description="Maximum research loop iterations")
    target_coverage: float = Field(default=0.85, ge=0.1, le=1.0, description="Target coverage threshold")
    min_new_relevant_papers: int = Field(default=1, ge=0, le=10, description="Min new papers per iteration")
    mock_mode: bool = Field(default=False, description="Run in mock mode using deterministic local fixtures")
    llm_provider: str = Field(default="mock", description="LLM provider: 'mock', 'openai', 'anthropic', 'gemini'")
    llm_model: Optional[str] = Field(default=None, description="Optional LLM model override")
    preferred_sources: List[str] = Field(
        default_factory=lambda: ["arxiv", "semantic_scholar", "crossref"],
        description="Target academic repositories"
    )
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="LLM temperature")


class CreateResearchRequest(BaseModel):
    """Request payload to initiate an autonomous literature review."""
    research_question: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="The scientific research question to investigate",
        examples=["What are current methods for factuality evaluation in retrieval-augmented generation?"]
    )
    config: Optional[ResearchConfigInput] = Field(
        default=None,
        description="Optional configuration overrides for this research run"
    )


class ResearchRunResponse(BaseModel):
    """Status and overview of a research run."""
    id: str
    research_question: str
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_iteration: int
    max_iterations: int
    coverage: float
    stopping_reason: Optional[str] = None
    error: Optional[str] = None
    total_papers: int = 0
    relevant_papers_count: int = 0
    themes_count: int = 0
    iterations_count: int = 0


class ResearchIterationResponse(BaseModel):
    """Detailed summary of a completed iteration."""
    id: str
    run_id: str
    iteration_number: int
    search_plan: Optional[dict[str, Any]] = None
    queries: List[str] = Field(default_factory=list)
    retrieved_count: int
    new_papers_count: int
    relevant_count: int
    coverage: float
    reflection: Optional[dict[str, Any]] = None
    created_at: datetime


class PaperResponse(BaseModel):
    """Normalized academic paper record."""
    id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    source: str
    citation_count: int = 0
    publication_date: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    is_relevant: Optional[bool] = None
    relevance_score: Optional[float] = None
    relevance_reason: Optional[str] = None
    iteration_number: Optional[int] = None


class ThemeResponse(BaseModel):
    """Thematic cluster discovered across literature."""
    id: str
    theme_id: str
    title: str
    description: str
    paper_ids: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    contradictions_or_tensions: List[str] = Field(default_factory=list)


class AgentEventResponse(BaseModel):
    """Structured telemetry event from the agent engine."""
    id: str
    run_id: str
    event_type: str
    iteration: int
    message: str
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class FinalReviewResponse(BaseModel):
    """Structured literature review synthesis suitable for display."""
    title: str
    narrative: str
    key_themes: List[dict[str, Any]] = Field(default_factory=list)
    consensus_findings: List[str] = Field(default_factory=list)
    open_research_gaps: List[str] = Field(default_factory=list)
    coherence_score: float = 0.0
    relevance_score: float = 0.0


class ResearchResultResponse(BaseModel):
    """Complete synthesized research output."""
    run_id: str
    research_question: str
    status: str
    coverage_score: float
    stop_reason: Optional[str] = None
    final_review: Optional[dict[str, Any]] = None
    synthesis: Optional[dict[str, Any]] = None
    reflection: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResponse(BaseModel):
    """System and literature evaluation dimensions."""
    run_id: str
    coverage: float
    relevance: float
    coherence: float
    citation_distribution: dict[str, Any] = Field(default_factory=dict)
    topic_coverage: Optional[float] = None
    paper_recall: Optional[float] = None
    evaluation_type: str = "intrinsic"
    benchmark_comparison: Optional[dict[str, Any]] = None
