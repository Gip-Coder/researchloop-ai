"""
Google Gemini LLM provider adapter using async HTTP client.
"""

from __future__ import annotations

import os
from typing import Any
import httpx

from backend.providers.llm.base import LLMProvider
from backend.agent.core.config import get_settings


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini Generative Language API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float = 0.2
    ):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        selected_model = model or settings.llm_model or "gemini-1.5-flash"
        super().__init__(model=selected_model, temperature=temperature)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"[System Instructions]:\n{system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will strictly follow these instructions."}]
            })
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                **kwargs
            }
        }

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini API.")
            return candidates[0]["content"]["parts"][0]["text"]

