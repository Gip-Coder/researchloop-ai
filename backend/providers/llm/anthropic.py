"""
Anthropic Claude LLM provider adapter using async HTTP client.
"""

from __future__ import annotations

import os
from typing import Any
import httpx

from backend.providers.llm.base import LLMProvider
from backend.agent.core.config import get_settings


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Messages API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.2
    ):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        selected_model = model or settings.llm_model or "claude-3-5-sonnet-20241022"
        super().__init__(model=selected_model, temperature=temperature)
        self.endpoint = "https://api.anthropic.com/v1/messages"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
