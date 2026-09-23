"""
Core state, configuration, and final result schemas for the research engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable
from pydantic import BaseModel, Field

from backend.agent.models.common import AgentEvent
from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan
from backend.agent.models.synthesis import Synthesis, Theme
from backend.agent.models.reflection import Reflection


class ResearchConfig(BaseModel):
    """Runtime configuration for ResearchEngine execution."""

    max_iterations: int = Field(default=3, description="Maximum research iterations before stopping")
    target_coverage: float = Field(default=0.85, ge=0.0, le=1.0, description="Target coverage score to achieve")
    min_new_relevant_papers: int = Field(
        default=1,
        description="Minimum new relevant papers needed in an iteration to prevent early stopping"
    )
    llm_provider: str = Field(default="mock", description="LLM provider: 'mock', 'openai', 'anthropic', 'gemini'")
    llm_model: str | None = Field(default=None, description="Optional model identifier override")
    preferred_sources: list[str] = Field(
        default_factory=lambda: ["arxiv", "semantic_scholar", "crossref"],
        description="Academic sources to query"
    )
    mock_mode: bool = Field(default=False, description="Enforce full mock mode without external network calls")
    temperature: float = Field(default=0.2, ge=0.0, le=1.0, description="LLM sampling temperature")
    academic_request_timeout: float = Field(default=15.0, description="Timeout in seconds for academic API queries")
    academic_max_retries: int = Field(default=3, description="Max retries with exponential backoff on provider failures")
    cache_enabled: bool = Field(default=True, description="Enable query and LLM result caching")
    event_callback: Any | None = Field(
        default=None,
        exclude=True,
        description="Optional async or sync callback for streaming AgentEvent notifications"
    )


class ResearchIteration(BaseModel):
    """Summary record of a completed iteration within the research loop."""

    iteration: int = Field(description="Iteration index (1-based)")
    search_plan: SearchPlan = Field(description="Search plan utilized in this iteration")
    queries_executed: list[str] = Field(default_factory=list, description="Queries dispatched across providers")
    papers_retrieved_count: int = Field(default=0, description="Total papers fetched in this iteration")
    new_papers_count: int = Field(default=0, description="New deduplicated papers added")
    relevant_papers_count: int = Field(default=0, description="Relevant papers retained")
    coverage_score: float = Field(default=0.0, description="Coverage score assessed at end of iteration")
    reflection: Reflection | None = Field(default=None, description="Critic evaluation for this iteration")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchState(BaseModel):
    """Mutable persistent state container tracking the complete research lifecycle."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    research_question: str = Field(description="The primary research question")
    iteration: int = Field(default=0, description="Current iteration index (0 = unstarted)")
    search_plan: SearchPlan | None = Field(default=None, description="Current or active search plan")
    papers: list[Paper] = Field(default_factory=list, description="All retrieved and deduplicated papers")
    relevant_papers: list[Paper] = Field(default_factory=list, description="Papers passing relevance criteria")
    themes: list[Theme] = Field(default_factory=list, description="Synthesized cross-paper themes")
    synthesis: Synthesis | None = Field(default=None, description="Active literature synthesis")
    reflection: Reflection | None = Field(default=None, description="Most recent critic reflection")
    coverage_score: float = Field(default=0.0, description="Current coverage score (0.0 to 1.0)")
    completed: bool = Field(default=False, description="Whether the research loop has concluded")
    stop_reason: str | None = Field(default=None, description="Reason for research termination")
    iteration_history: list[ResearchIteration] = Field(default_factory=list, description="History of all iterations")
    events: list[AgentEvent] = Field(default_factory=list, description="Complete event log")


class ResearchResult(BaseModel):
    """Frozen public integration contract returned by ResearchEngine.run() to Member 2."""

    session_id: str = Field(description="Unique identifier for the research session")
    status: str = Field(description="'completed' or 'failed'")
    research_question: str = Field(description="Original research question")
    iterations: list[ResearchIteration] = Field(default_factory=list, description="Per-iteration audit log")
    papers: list[Paper] = Field(default_factory=list, description="All deduplicated papers discovered")
    relevant_papers: list[Paper] = Field(default_factory=list, description="Curated relevant papers")
    themes: list[Theme] = Field(default_factory=list, description="Dynamically identified research themes")
    synthesis: Synthesis | None = Field(default=None, description="Final literature synthesis")
    reflection: Reflection | None = Field(default=None, description="Final critic evaluation")
    final_review: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured review summary suitable for frontend rendering"
    )
    coverage_score: float = Field(default=0.0, description="Final estimated research coverage score")
    stop_reason: str | None = Field(default=None, description="Human-readable reason for stopping")
    events: list[AgentEvent] = Field(default_factory=list, description="Chronological trace of agent events")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Execution parameters and metrics")

