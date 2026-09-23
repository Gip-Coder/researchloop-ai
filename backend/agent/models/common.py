"""
Common models, enums, and event schemas for the agent engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Canonical event types emitted throughout the research loop."""

    RESEARCH_STARTED = "research.started"
    PLANNER_STARTED = "planner.started"
    PLANNER_COMPLETED = "planner.completed"

    RETRIEVAL_STARTED = "retrieval.started"
    RETRIEVAL_COMPLETED = "retrieval.completed"
    RETRIEVAL_FAILED = "retrieval.failed"

    FILTER_COMPLETED = "filter.completed"

    SYNTHESIS_STARTED = "synthesis.started"
    SYNTHESIS_COMPLETED = "synthesis.completed"

    REFLECTION_STARTED = "reflection.started"
    REFLECTION_COMPLETED = "reflection.completed"

    REPLANNING_STARTED = "replanning.started"
    REPLANNING_COMPLETED = "replanning.completed"

    RESEARCH_COMPLETED = "research.completed"
    RESEARCH_FAILED = "research.failed"


class AgentEvent(BaseModel):
    """Structured event record emitted by the engine for telemetry and UI traces."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(description="One of EventType values")
    iteration: int = Field(default=0, description="Iteration number (0 for initialization)")
    message: str = Field(description="Human-readable description of event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary context data")


class DateRange(BaseModel):
    """Publication date filtering bounds."""

    start_year: int | None = Field(default=None, description="Earliest publication year inclusive")
    end_year: int | None = Field(default=None, description="Latest publication year inclusive")
