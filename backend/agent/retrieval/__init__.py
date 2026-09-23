"""
Academic retrieval provider adapters and multi-source retriever.
"""

from backend.agent.retrieval.base import AcademicSource
from backend.agent.retrieval.mock_retriever import MockAcademicProvider
from backend.agent.retrieval.semantic_scholar import SemanticScholarProvider
from backend.agent.retrieval.arxiv import ArxivProvider
from backend.agent.retrieval.crossref import CrossrefProvider
from backend.agent.retrieval.multi_retriever import MultiProviderRetriever

__all__ = [
    "AcademicSource",
    "MockAcademicProvider",
    "SemanticScholarProvider",
    "ArxivProvider",
    "CrossrefProvider",
    "MultiProviderRetriever",
]
