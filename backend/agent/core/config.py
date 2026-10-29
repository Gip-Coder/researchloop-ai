"""
Configuration management for the research agent engine.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Automatically search for .env in current and parent directories
load_dotenv(override=False)

VALID_ACADEMIC_SOURCES = {"arxiv", "crossref", "semantic_scholar"}


def parse_preferred_sources(raw: str | None) -> list[str]:
    """Parse, normalize, and validate comma-separated preferred sources string."""
    if not raw:
        return ["arxiv", "crossref"]
    cleaned: list[str] = []
    for item in raw.split(","):
        s = item.strip().lower()
        if not s:
            continue
        if s in VALID_ACADEMIC_SOURCES:
            if s not in cleaned:
                cleaned.append(s)
        else:
            logger.warning(
                f"Unknown academic source '{s}' in PREFERRED_SOURCES ignored. "
                f"Valid sources: {sorted(list(VALID_ACADEMIC_SOURCES))}"
            )
    return cleaned or ["arxiv", "crossref"]


class AgentSettings(BaseModel):
    """Core settings for researchloop-ai Agent Engine."""

    # Operational mode ('mock' or 'live')
    researchloop_mode: str = Field(
        default_factory=lambda: os.getenv("RESEARCHLOOP_MODE", "mock").lower()
    )

    # Active LLM Provider ('mock', 'openai', 'anthropic', 'gemini', 'ollama')
    llm_provider: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "mock").lower()
    )
    llm_model: str | None = Field(
        default_factory=lambda: os.getenv("LLM_MODEL", None)
    )

    # Academic Retrieval Sources (default excludes semantic_scholar)
    preferred_sources: list[str] = Field(
        default_factory=lambda: parse_preferred_sources(os.getenv("PREFERRED_SOURCES", "arxiv,crossref"))
    )

    # API Keys
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", None)
    )
    anthropic_api_key: str | None = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", None)
    )
    gemini_api_key: str | None = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", None)
    )
    ollama_base_url: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    )
    semantic_scholar_api_key: str | None = Field(
        default_factory=lambda: os.getenv("SEMANTIC_SCHOLAR_API_KEY", None)
    )
    crossref_mailto: str | None = Field(
        default_factory=lambda: os.getenv("CROSSREF_MAILTO", "researchloop@example.com")
    )

    # Hyperparameters
    default_max_iterations: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_MAX_ITERATIONS", "3"))
    )
    default_target_coverage: float = Field(
        default_factory=lambda: float(os.getenv("DEFAULT_TARGET_COVERAGE", "0.85"))
    )
    default_min_new_papers: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_MIN_NEW_PAPERS", "1"))
    )
    academic_request_timeout: float = Field(
        default_factory=lambda: float(os.getenv("ACADEMIC_REQUEST_TIMEOUT", "15.0"))
    )
    academic_max_retries: int = Field(
        default_factory=lambda: int(os.getenv("ACADEMIC_MAX_RETRIES", "3"))
    )

    # Research Quality & Paper Selection Hyperparameters
    default_min_publication_year: int | None = Field(
        default_factory=lambda: int(os.getenv("MIN_PUBLICATION_YEAR")) if os.getenv("MIN_PUBLICATION_YEAR") and os.getenv("MIN_PUBLICATION_YEAR").strip().lower() not in ("none", "0", "") else None
    )
    default_min_citations: int = Field(
        default_factory=lambda: int(os.getenv("MIN_CITATIONS", "5"))
    )
    default_allow_unknown_citations: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_UNKNOWN_CITATIONS", "true").lower() in ("1", "true", "yes")
    )
    default_preferred_min_citations: int = Field(
        default_factory=lambda: int(os.getenv("PREFERRED_MIN_CITATIONS", "10"))
    )
    default_preferred_max_citations: int = Field(
        default_factory=lambda: int(os.getenv("PREFERRED_MAX_CITATIONS", "15"))
    )
    default_strict_citation_filtering: bool = Field(
        default_factory=lambda: os.getenv("STRICT_CITATION_FILTERING", "false").lower() in ("1", "true", "yes")
    )
    default_min_synthesis_papers: int = Field(
        default_factory=lambda: int(os.getenv("MIN_SYNTHESIS_PAPERS", "6"))
    )
    default_target_synthesis_papers: int = Field(
        default_factory=lambda: int(os.getenv("TARGET_SYNTHESIS_PAPERS", "8"))
    )
    default_max_synthesis_papers: int = Field(
        default_factory=lambda: int(os.getenv("MAX_SYNTHESIS_PAPERS", "10"))
    )
    default_allow_foundational_exceptions: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_FOUNDATIONAL_EXCEPTIONS", "false").lower() in ("1", "true", "yes")
    )

    # Cache Settings
    research_cache_enabled: bool = Field(
        default_factory=lambda: os.getenv("RESEARCH_CACHE_ENABLED", "true").lower() in ("1", "true", "yes")
    )
    cache_dir: str = Field(
        default_factory=lambda: os.getenv("CACHE_DIR", ".cache/researchloop")
    )

    @property
    def is_mock_mode(self) -> bool:
        return self.researchloop_mode == "mock" or self.llm_provider == "mock"


_SETTINGS_INSTANCE: AgentSettings | None = None


def get_settings(reload: bool = False) -> AgentSettings:
    """Return singleton or freshly loaded settings instance."""
    global _SETTINGS_INSTANCE
    if _SETTINGS_INSTANCE is None or reload:
        _SETTINGS_INSTANCE = AgentSettings()
    return _SETTINGS_INSTANCE
