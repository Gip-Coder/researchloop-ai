"""
OpenAI LLM provider adapter using async HTTP client.
"""

from __future__ import annotations

import os
from typing import Any
import httpx

from backend.providers.llm.base import LLMProvider
from backend.agent.core.config import get_settings


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API chat completions."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        base_url: str = "https://api.openai.com/v1"
    ):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        selected_model = model or settings.llm_model or "gpt-4o-mini"
        super().__init__(model=selected_model, temperature=temperature)
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **kwargs
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

