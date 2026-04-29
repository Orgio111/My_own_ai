"""Tracks token consumption per model so we can expose usage gauges."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict


@dataclass
class Usage:
    prompt: int = 0
    completion: int = 0
    total: int = 0
    requests: int = 0


class TokenTracker:
    def __init__(self, window_sec: int = 60) -> None:
        self.window = window_sec
        self.totals: Dict[str, Usage] = defaultdict(Usage)
        self._window: Dict[str, Deque[tuple[float, int]]] = defaultdict(deque)

    def record(self, model: str, prompt: int, completion: int) -> None:
        u = self.totals[model]
        u.prompt += prompt
        u.completion += completion
        u.total += prompt + completion
        u.requests += 1
        now = time.monotonic()
        self._window[model].append((now, prompt + completion))
        self._gc(model, now)

    def _gc(self, model: str, now: float) -> None:
        dq = self._window[model]
        while dq and now - dq[0][0] > self.window:
            dq.popleft()

    def per_minute(self, model: str) -> int:
        now = time.monotonic()
        self._gc(model, now)
        return sum(t for _, t in self._window[model])

    def snapshot(self) -> Dict[str, Dict[str, int]]:
        return {
            m: {
                "prompt": u.prompt,
                "completion": u.completion,
                "total": u.total,
                "requests": u.requests,
                "tokens_per_min": self.per_minute(m),
            }
            for m, u in self.totals.items()
        }


tracker = TokenTracker()
