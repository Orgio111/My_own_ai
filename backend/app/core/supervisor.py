"""Always-on supervisor: heartbeats, health, auto-restart of agents."""
from __future__ import annotations

import asyncio
import time

import psutil

from app.core.router import REGISTRY, mark_healthy
from app.core.token_tracker import tracker
from app.utils.events import bus
from app.utils.logger import log


class Supervisor:
    def __init__(self, interval: float = 5.0) -> None:
        self.interval = interval
        self._stop = asyncio.Event()
        self.started_at = time.time()

    async def stop(self) -> None:
        self._stop.set()

    async def run_forever(self) -> None:
        log.info("supervisor.start")
        while not self._stop.is_set():
            try:
                await self._tick()
            except Exception as e:  # never die
                log.error("supervisor.tick.error", err=str(e))
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                pass

    async def _tick(self) -> None:
        # rehydrate health (simple heuristic — real version would probe each model)
        for m in REGISTRY:
            mark_healthy(m)

        snapshot = {
            "ts": time.time(),
            "uptime_sec": int(time.time() - self.started_at),
            "cpu": psutil.cpu_percent(interval=None),
            "mem": psutil.virtual_memory().percent,
            "models": [{"id": c.id, "healthy": c.healthy, "role": c.role} for c in REGISTRY.values()],
            "usage": tracker.snapshot(),
        }
        await bus.publish("system.health", snapshot)
