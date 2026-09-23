"""
Mocked unit tests for LLM providers and JSON schema validation (100% offline).
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from backend.providers.llm.base import LLMProvider
from backend.providers.llm.mock import MockLLMProvider
from backend.providers.llm.factory import get_llm_provider
from backend.agent.models.research import ResearchConfig


class SampleModel(BaseModel):
    name: str
    count: int
    is_active: bool


class MockCustomLLM(LLMProvider):
    """Subclass returning customizable test responses."""

    def __init__(self, responses: list[str]):
        super().__init__(model="test")
        self.responses = list(responses)
        self.call_count = 0

    async def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str:
        self.call_count += 1
        if self.responses:
            return self.responses.pop(0)
        return "{}"


def test_extract_json_varieties():
    llm = MockLLMProvider()

    # 1. Clean JSON
    assert llm._extract_json('{"key": "val"}') == {"key": "val"}

    # 2. Markdown fenced code block
    fenced = """Here is the result:
```json
{
  "key": "val"
}
```
Hope this helps!"""
    assert llm._extract_json(fenced) == {"key": "val"}

    # 3. Preamble with unclosed conversational text
    messy = 'Sure! Here is the JSON: {"number": 42, "status": "ok"} Thank you!'
    assert llm._extract_json(messy) == {"number": 42, "status": "ok"}

    # 4. JSON array
    arr_text = "Result: [1, 2, 3]"
    assert llm._extract_json(arr_text) == [1, 2, 3]

    # 5. Invalid text
    assert llm._extract_json("not json at all") is None


@pytest.mark.asyncio
async def test_generate_structured_retry_on_initial_malformed():
    """Verify that generate_structured retries when the first output is invalid JSON."""
    llm = MockCustomLLM(
        responses=[
            "Sorry, I forgot to format as JSON! The name is Alice.",  # Attempt 1: invalid
            '{"name": "Alice", "count": 10, "is_active": true}'     # Attempt 2: valid
        ]
    )

    result = await llm.generate_structured(
        prompt="Get user",
        response_model=SampleModel,
        max_retries=2
    )

    assert result.name == "Alice"
    assert result.count == 10
    assert result.is_active is True
    assert llm.call_count == 2


@pytest.mark.asyncio
async def test_generate_structured_fails_after_retries():
    """Verify ValueError is raised if all retry attempts fail."""
    llm = MockCustomLLM(
        responses=[
            "invalid 1",
            "invalid 2",
            "invalid 3"
        ]
    )

    with pytest.raises(ValueError, match="Failed to produce valid structured output"):
        await llm.generate_structured(
            prompt="Get user",
            response_model=SampleModel,
            max_retries=2
        )


def test_factory_returns_mock_when_configured():
    config = ResearchConfig(mock_mode=True)
    provider = get_llm_provider(config)
    assert isinstance(provider, MockLLMProvider)
