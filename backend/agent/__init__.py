"""
researchloop-ai agent package
Exposes the public engine interface and shared contract models.
"""

from backend.agent.models.research import (
    ResearchConfig,
    ResearchResult,
    ResearchState,
    ResearchIteration,
)
from backend.agent.models.paper import Paper, PaperRelevance
from backend.agent.models.search import SearchPlan
from backend.agent.models.synthesis import Synthesis, Theme, PaperAnalysis
from backend.agent.models.reflection import Reflection
from backend.agent.models.common import AgentEvent, EventType

try:
    from backend.agent.orchestration.engine import ResearchEngine
except ImportError:
    ResearchEngine = None  # Will be fully populated once engine is imported

__all__ = [
    "ResearchEngine",
    "ResearchConfig",
    "ResearchResult",
    "ResearchState",
    "ResearchIteration",
    "Paper",
    "PaperRelevance",
    "SearchPlan",
    "Synthesis",
    "Theme",
    "PaperAnalysis",
    "Reflection",
    "AgentEvent",
    "EventType",
]

