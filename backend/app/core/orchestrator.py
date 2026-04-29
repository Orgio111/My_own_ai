"""Multi-model orchestration: route, parallel, chain."""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional

from app.core.nvidia_client import nvidia
from app.core.rate_limiter import limiter
from app.core.router import mark_unhealthy, pick
from app.core.token_tracker import tracker
from app.utils.events import bus
from app.utils.logger import log


class Orchestrator:
    """Single entrypoint used by agents and the API layer."""

    async def complete(
        self,
        messages: List[Dict[str, Any]],
        *,
        task_class: str = "reasoning",
        model_override: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        card = pick(task_class, override=model_override)
        await limiter.acquire(card.id, tokens=1)
        await bus.publish("model.call", {"model": card.id, "task_class": task_class})
        try:
            res = await nvidia.chat(
                card.id, messages, temperature=temperature, max_tokens=max_tokens
            )
            usage = res.get("usage") or {}
            tracker.record(
                card.id,
                int(usage.get("prompt_tokens", 0)),
                int(usage.get("completion_tokens", 0)),
            )
            content = res["choices"][0]["message"]["content"]
            return {"model": card.id, "content": content, "usage": usage, "raw": res}
        except Exception as e:
            log.warning("orchestrator.fail", model=card.id, err=str(e))
            mark_unhealthy(card.id)
            raise

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        *,
        task_class: str = "reasoning",
        model_override: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        card = pick(task_class, override=model_override)
        await limiter.acquire(card.id, tokens=1)
        await bus.publish("model.stream.start", {"model": card.id})
        try:
            async for tok in nvidia.chat_stream(
                card.id, messages, temperature=temperature, max_tokens=max_tokens
            ):
                yield tok
        finally:
            await bus.publish("model.stream.end", {"model": card.id})

    async def fan_out(
        self,
        messages: List[Dict[str, Any]],
        models: List[str],
        *,
        max_tokens: int = 512,
    ) -> List[Dict[str, Any]]:
        """Ask N models in parallel; return all answers (caller can vote/merge)."""
        async def one(m: str) -> Dict[str, Any]:
            try:
                return await self.complete(messages, model_override=m, max_tokens=max_tokens)
            except Exception as e:
                return {"model": m, "error": str(e)}
        return await asyncio.gather(*(one(m) for m in models))

    async def chain(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sequentially chain calls — `messages` of step N may reference output of N-1."""
        results: List[Dict[str, Any]] = []
        carry = ""
        for step in steps:
            msgs = step["messages"]
            if carry and step.get("inject_previous"):
                msgs = msgs + [{"role": "user", "content": f"Previous output:\n{carry}"}]
            r = await self.complete(
                msgs,
                task_class=step.get("task_class", "reasoning"),
                model_override=step.get("model"),
                max_tokens=step.get("max_tokens", 1024),
            )
            results.append(r)
            carry = r["content"]
        return results


orchestrator = Orchestrator()
