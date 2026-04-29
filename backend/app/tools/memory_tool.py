"""Memory tools registered as agent capabilities."""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.executor import register_tool
from app.memory.store import store


async def memory_search(query: str, k: int = 5) -> List[Dict[str, Any]]:
    return await store.search(query, k=k)


async def memory_write(key: str, value: str) -> str:
    await store.upsert(key, value)
    return f"saved memory {key} ({len(value)} chars)"


register_tool("memory.search", memory_search)
register_tool("memory.write", memory_write)
