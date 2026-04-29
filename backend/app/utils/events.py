"""In-process pub/sub event bus. Used by agents to stream traces to the WS layer."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, AsyncIterator, Dict, List


class EventBus:
    def __init__(self) -> None:
        self._subs: Dict[str, List[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, topic: str = "*") -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=1024)
        self._subs[topic].append(q)
        return q

    def unsubscribe(self, topic: str, q: asyncio.Queue) -> None:
        if q in self._subs.get(topic, []):
            self._subs[topic].remove(q)

    async def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        msg = {"topic": topic, **payload}
        for t in (topic, "*"):
            for q in list(self._subs.get(t, [])):
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await q.put(msg)

    async def stream(self, topic: str = "*") -> AsyncIterator[Dict[str, Any]]:
        q = self.subscribe(topic)
        try:
            while True:
                yield await q.get()
        finally:
            self.unsubscribe(topic, q)


bus = EventBus()
