"""
Shared data models forming the frozen contract for researchloop-ai.
"""

from backend.agent.models.common import AgentEvent, EventType, DateRange
from backend.agent.models.paper import Paper
from backend.agent.models.search import SearchPlan, SearchQuery
from backend.agent.models.synthesis import Synthesis, Theme, PaperAnalysis, CrossPaperInsight
from backend.agent.models.reflection import Reflection
from backend.agent.models.research import (
    ResearchConfig,
    ResearchIteration,
    ResearchState,
    ResearchResult,
)

__all__ = [
    "AgentEvent",
    "EventType",
    "DateRange",
    "Paper",
    "SearchPlan",
    "SearchQuery",
    "Synthesis",
    "Theme",
    "PaperAnalysis",
    "CrossPaperInsight",
    "Reflection",
    "ResearchConfig",
    "ResearchIteration",
    "ResearchState",
    "ResearchResult",
]

