"""
Filtering and deduplication modules for academic paper processing.
"""

from backend.agent.filtering.deduplication import Deduplicator
from backend.agent.filtering.relevance import RelevanceFilter

__all__ = ["Deduplicator", "RelevanceFilter"]

