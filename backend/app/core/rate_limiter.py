"""Per-model token-bucket rate limiter."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Bucket:
    capacity: int
    refill_per_sec: float
    tokens: float = field(init=False)
    updated: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)

    def take(self, n: int) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.refill_per_sec)
        self.updated = now
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: Dict[str, Bucket] = {}
        self._lock = asyncio.Lock()

    def configure(self, model: str, capacity: int, refill_per_sec: float) -> None:
        self._buckets[model] = Bucket(capacity, refill_per_sec)

    async def acquire(self, model: str, tokens: int = 1) -> None:
        bucket = self._buckets.setdefault(model, Bucket(60, 1.0))
        while True:
            async with self._lock:
                if bucket.take(tokens):
                    return
            await asyncio.sleep(0.25)


limiter = RateLimiter()
