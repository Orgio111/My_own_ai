"""Executor: runs each step of a plan via the tool registry."""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict

from app.agents.base import Plan, Step, StepStatus
from app.agents.modes import AgentMode, requires_approval
from app.core.orchestrator import orchestrator
from app.utils.events import bus
from app.utils.logger import log

# Lazy registry — avoids circular imports
_TOOLS: Dict[str, Callable[..., Awaitable[Any]]] = {}


def register_tool(name: str, fn: Callable[..., Awaitable[Any]]) -> None:
    _TOOLS[name] = fn


async def _builtin_llm_ask(prompt: str, task_class: str = "reasoning") -> str:
    res = await orchestrator.complete(
        [{"role": "user", "content": prompt}],
        task_class=task_class,
        max_tokens=800,
    )
    return res["content"]


# default builtin tool
register_tool("llm.ask", _builtin_llm_ask)


class Approval:
    """Coordinates per-step approval when in guided/manual mode."""

    def __init__(self) -> None:
        self._waiters: Dict[str, asyncio.Future] = {}

    async def wait(self, step_id: str) -> bool:
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._waiters[step_id] = fut
        try:
            return await fut
        finally:
            self._waiters.pop(step_id, None)

    def resolve(self, step_id: str, ok: bool) -> bool:
        fut = self._waiters.get(step_id)
        if not fut or fut.done():
            return False
        fut.set_result(ok)
        return True


approval = Approval()


async def execute(plan: Plan, mode: AgentMode = AgentMode.GUIDED) -> Plan:
    await bus.publish("plan.start", {"plan": plan.to_dict()})
    for step in plan.steps:
        await _run_step(plan, step, mode)
        if step.status == StepStatus.FAILED:
            log.error("executor.step.fail", step=step.id, err=step.error)
            break
    await bus.publish("plan.done", {"plan": plan.to_dict()})
    return plan


async def _run_step(plan: Plan, step: Step, mode: AgentMode) -> None:
    tool = step.tool or "llm.ask"
    fn = _TOOLS.get(tool)
    if fn is None:
        step.status = StepStatus.FAILED
        step.error = f"unknown tool: {tool}"
        await bus.publish("step.update", {"plan_id": plan.id, "step": _serialize(step)})
        return

    if requires_approval(mode, tool):
        step.status = StepStatus.AWAITING
        await bus.publish("step.update", {"plan_id": plan.id, "step": _serialize(step)})
        await bus.publish(
            "approval.request",
            {"plan_id": plan.id, "step_id": step.id, "tool": tool, "args": step.args, "description": step.description},
        )
        try:
            ok = await asyncio.wait_for(approval.wait(step.id), timeout=300)
        except asyncio.TimeoutError:
            ok = False
        if not ok:
            step.status = StepStatus.SKIPPED
            await bus.publish("step.update", {"plan_id": plan.id, "step": _serialize(step)})
            return

    step.status = StepStatus.RUNNING
    await bus.publish("step.update", {"plan_id": plan.id, "step": _serialize(step)})
    try:
        result = await fn(**(step.args or {}))
        step.result = _truncate(result)
        step.status = StepStatus.DONE
    except Exception as e:
        step.status = StepStatus.FAILED
        step.error = str(e)
    await bus.publish("step.update", {"plan_id": plan.id, "step": _serialize(step)})


def _serialize(step: Step) -> Dict[str, Any]:
    return {
        "id": step.id,
        "description": step.description,
        "tool": step.tool,
        "args": step.args,
        "status": step.status.value,
        "result": step.result,
        "error": step.error,
    }


def _truncate(v: Any, limit: int = 4000) -> Any:
    if isinstance(v, str) and len(v) > limit:
        return v[:limit] + f"\n... [truncated {len(v) - limit} chars]"
    return v
