"""
Configuration management for the research agent engine.
"""

from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Automatically search for .env in current and parent directories
load_dotenv(override=False)


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


def get_settings() -> AgentSettings:
    """Return singleton or freshly loaded settings instance."""
    global _SETTINGS_INSTANCE
    if _SETTINGS_INSTANCE is None:
        _SETTINGS_INSTANCE = AgentSettings()
    return _SETTINGS_INSTANCE

