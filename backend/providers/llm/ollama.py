"""Local Ollama provider using its native chat and JSON-schema API."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from backend.agent.core.config import get_settings
from backend.providers.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Generate completions locally through Ollama's HTTP API."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.2,
        base_url: str | None = None,
    ):
        settings = get_settings()
        selected_model = model or settings.llm_model or "llama3.2:3b"
        super().__init__(model=selected_model, temperature=temperature)
        self.base_url = (
            base_url or settings.ollama_base_url or os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434"
        ).rstrip("/")

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if "format" in kwargs:
            payload["format"] = kwargs["format"]

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        content = data.get("message", {}).get("content")
        if not isinstance(content, str):
            raise ValueError("Ollama returned no message content.")
        return content

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: str | None = None,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> Any:
        """Request schema-constrained JSON from Ollama and validate it with Pydantic."""
        schema = response_model.model_json_schema()
        augmented_system = (system_prompt or "") + (
            "\n\nReturn only a JSON object matching the required response schema."
        )
        current_prompt = prompt
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            raw = await self.generate(
                prompt=current_prompt,
                system_prompt=augmented_system,
                format=schema,
            )
            try:
                return response_model.model_validate(json.loads(raw))
            except (json.JSONDecodeError, ValidationError, TypeError) as err:
                last_error = err
                current_prompt = (
                    f"{prompt}\n\nYour previous response did not match the required schema: {err}. "
                    "Return a corrected JSON object only."
                )

        raise ValueError(
            f"Ollama failed to return valid {response_model.__name__} JSON after "
            f"{max_retries + 1} attempts: {last_error}"
        )
