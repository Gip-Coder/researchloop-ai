"""
Base abstract interface for LLM providers.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import TypeVar, Any
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract base class for all LLM providers supporting text and structured schemas."""

    def __init__(self, model: str | None = None, temperature: float = 0.2):
        self.model = model
        self.temperature = temperature

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        """Generate unstructured completion."""
        pass

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        max_retries: int = 2,
        **kwargs: Any
    ) -> T:
        """
        Generate structured output validated against a Pydantic model.
        Includes automatic JSON extraction, validation, and schema-guided retry on malformed outputs.
        """
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        augmented_system = (system_prompt or "") + (
            f"\n\nCRITICAL: Respond ONLY with a valid JSON object strictly complying with this JSON Schema:\n{schema_json}\n"
            "Do NOT include markdown explanation or introductory commentary outside the JSON."
        )

        last_error = None
        current_prompt = prompt

        for attempt in range(max_retries + 1):
            raw_response = await self.generate(
                prompt=current_prompt,
                system_prompt=augmented_system,
                **kwargs
            )

            parsed_data = self._extract_json(raw_response)
            if parsed_data is not None:
                try:
                    return response_model.model_validate(parsed_data)
                except ValidationError as val_err:
                    last_error = val_err
                    current_prompt = (
                        f"{prompt}\n\n[SYSTEM RECOVERY ATTEMPT {attempt + 1}]: "
                        f"Your previous output failed validation: {val_err}. "
                        "Please correct the fields and output the strictly valid JSON object."
                    )
            else:
                last_error = ValueError(f"Could not extract JSON from LLM response: {raw_response[:200]}")
                current_prompt = (
                    f"{prompt}\n\n[SYSTEM RECOVERY ATTEMPT {attempt + 1}]: "
                    "Your response was not valid JSON. Ensure you return ONLY valid JSON."
                )

        raise ValueError(
            f"Failed to produce valid structured output for {response_model.__name__} "
            f"after {max_retries + 1} attempts. Last error: {last_error}"
        )

    def _extract_json(self, text: str) -> dict[str, Any] | list[Any] | None:
        """Extract and parse JSON from a response string, stripping code blocks or preamble."""
        text = text.strip()
        if not text:
            return None

        # Check for ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # Search for outermost matching braces { ... }
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx : end_idx + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # Search for outermost brackets [ ... ]
        start_b = text.find("[")
        end_b = text.rfind("]")
        if start_b != -1 and end_b != -1 and end_b > start_b:
            candidate = text[start_b : end_b + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        return None
