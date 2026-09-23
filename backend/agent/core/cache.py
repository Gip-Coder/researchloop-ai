"""
Query and LLM response caching layer with stable SHA-256 keying.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from backend.agent.core.config import get_settings


class QueryCache:
    """Stable key-value cache supporting memory and disk persistence."""

    def __init__(self, cache_dir: str | None = None, enabled: bool | None = None):
        settings = get_settings()
        self.enabled = settings.research_cache_enabled if enabled is None else enabled
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self._memory_cache: dict[str, Any] = {}

        if self.enabled:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    def _hash_key(self, namespace: str, key_data: Any) -> str:
        """Generate a deterministic SHA-256 hash for the given namespace and key data."""
        if isinstance(key_data, (dict, list)):
            serialized = json.dumps(key_data, sort_keys=True, default=str)
        else:
            serialized = str(key_data)
        raw = f"{namespace}:{serialized}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def get(self, namespace: str, key_data: Any) -> Any | None:
        """Retrieve cached value if present, else None."""
        if not self.enabled:
            return None

        cache_key = self._hash_key(namespace, key_data)

        # 1. Check memory
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # 2. Check disk
        file_path = self.cache_dir / f"{namespace}_{cache_key}.json"
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                data = json.loads(content)
                self._memory_cache[cache_key] = data
                return data
            except Exception:
                return None

        return None

    async def set(self, namespace: str, key_data: Any, value: Any) -> None:
        """Store value in memory and on disk."""
        if not self.enabled:
            return

        cache_key = self._hash_key(namespace, key_data)
        self._memory_cache[cache_key] = value

        file_path = self.cache_dir / f"{namespace}_{cache_key}.json"
        try:
            serialized = json.dumps(value, indent=2, default=str)
            file_path.write_text(serialized, encoding="utf-8")
        except Exception:
            # Non-fatal if disk write fails
            pass

    def clear(self) -> None:
        """Clear memory cache."""
        self._memory_cache.clear()
