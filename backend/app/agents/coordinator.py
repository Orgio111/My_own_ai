"""Coordinator: registers agents, dispatches goals, supports collaboration."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.agents.base import Plan, new_id
from app.agents.critic import critique
from app.agents.executor import execute
from app.agents.modes import AgentMode
from app.agents.planner import plan as plan_goal
from app.config import settings
from app.utils.events import bus
from app.utils.logger import log


@dataclass
class AgentRecord:
    id: str
    name: str
    mode: AgentMode
    role: str = "general"
    busy: bool = False
    last_plan: Optional[Plan] = None
    history: List[Plan] = field(default_factory=list)


class Coordinator:
    def __init__(self) -> None:
        self.agents: Dict[str, AgentRecord] = {}
        self._sem = asyncio.Semaphore(settings.max_parallel_agents)
        self._lock = asyncio.Lock()

    def spawn(self, name: str = "agent", role: str = "general", mode: Optional[AgentMode] = None) -> AgentRecord:
        rec = AgentRecord(
            id=new_id("agent"),
            name=name,
            role=role,
            mode=mode or AgentMode(settings.default_agent_mode),
        )
        self.agents[rec.id] = rec
        return rec

    def list(self) -> List[Dict]:
        return [
            {"id": a.id, "name": a.name, "role": a.role, "mode": a.mode.value, "busy": a.busy}
            for a in self.agents.values()
        ]

    def set_mode(self, agent_id: str, mode: AgentMode) -> None:
        if agent_id in self.agents:
            self.agents[agent_id].mode = mode

    async def run(self, agent_id: str, goal: str, *, max_iters: int = 2) -> Plan:
        if agent_id not in self.agents:
            raise KeyError(agent_id)
        rec = self.agents[agent_id]

        async with self._sem:
            async with self._lock:
                rec.busy = True
                await bus.publish("agent.busy", {"agent_id": agent_id, "busy": True})
            try:
                final: Optional[Plan] = None
                current_goal = goal
                for i in range(max_iters):
                    p = await plan_goal(current_goal)
                    rec.last_plan = p
                    p = await execute(p, mode=rec.mode)
                    final = p
                    rec.history.append(p)
                    verdict = await critique(p)
                    await bus.publish("agent.critique", {"agent_id": agent_id, "verdict": verdict})
                    if verdict.get("verdict") == "achieved":
                        break
                    next_goal = verdict.get("next_goal")
                    if not next_goal:
                        break
                    current_goal = next_goal
                    log.info("coordinator.replan", agent=agent_id, iter=i + 1)
                return final  # type: ignore[return-value]
            finally:
                rec.busy = False
                await bus.publish("agent.busy", {"agent_id": agent_id, "busy": False})

    async def delegate(self, from_id: str, goal: str, role: str = "general") -> Plan:
        """Spawn a sub-agent and run a goal through it."""
        sub = self.spawn(name=f"sub-of-{from_id}", role=role)
        await bus.publish("agent.delegate", {"from": from_id, "to": sub.id, "goal": goal})
        return await self.run(sub.id, goal)


coordinator = Coordinator()
