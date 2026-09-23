"""
Base abstract class for academic providers with built-in retry and resilience.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine
import httpx

from backend.agent.models.paper import Paper

logger = logging.getLogger(__name__)


class AcademicSource(ABC):
    """Abstract base class for all academic literature search providers."""

    def __init__(
        self,
        name: str,
        timeout: float = 15.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5
    ):
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        start_year: int | None = None,
        end_year: int | None = None,
        **kwargs: Any
    ) -> list[Paper]:
        """Search the academic source and return normalized Paper models."""
        pass

    async def _execute_with_retry(
        self,
        request_func: Callable[[], Coroutine[Any, Any, httpx.Response]]
    ) -> httpx.Response:
        """
        Executes an HTTP request with exponential backoff, rate-limit awareness (HTTP 429),
        and timeout handling.
        """
        delay = 1.0
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = await request_func()

                # Handle HTTP 429 Rate Limit
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    sleep_time = float(retry_after) if retry_after and retry_after.isdigit() else delay * 2
                    logger.warning(
                        f"[{self.name}] Rate limit (429) encountered. Sleeping {sleep_time:.1f}s before attempt {attempt + 1}"
                    )
                    await asyncio.sleep(sleep_time)
                    delay *= self.backoff_factor
                    continue

                response.raise_for_status()
                return response

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as err:
                last_exception = err
                logger.warning(
                    f"[{self.name}] Network/Timeout failure on attempt {attempt + 1}/{self.max_retries}: {err}. Retrying in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
                delay *= self.backoff_factor

            except httpx.HTTPStatusError as err:
                last_exception = err
                # If 5xx server error, retry with backoff; if 4xx (other than 429), fail immediately
                if 500 <= err.response.status_code < 600:
                    logger.warning(
                        f"[{self.name}] Server error {err.response.status_code} on attempt {attempt + 1}. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    delay *= self.backoff_factor
                else:
                    raise err

        raise RuntimeError(
            f"[{self.name}] Exhausted all {self.max_retries} attempts. Last error: {last_exception}"
        )
