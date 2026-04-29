"""Agent API — spawn, run, mode, list, approve."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.coordinator import coordinator
from app.agents.executor import approval
from app.agents.modes import AgentMode

router = APIRouter()


class SpawnRequest(BaseModel):
    name: str = "agent"
    role: str = "general"
    mode: Optional[str] = None


class RunRequest(BaseModel):
    agent_id: str
    goal: str
    max_iters: int = 2


class ModeRequest(BaseModel):
    agent_id: str
    mode: str


class ApprovalRequest(BaseModel):
    step_id: str
    approved: bool


@router.get("")
async def list_agents():
    return coordinator.list()


@router.post("/spawn")
async def spawn(req: SpawnRequest):
    mode = AgentMode(req.mode) if req.mode else None
    rec = coordinator.spawn(name=req.name, role=req.role, mode=mode)
    return {"id": rec.id, "name": rec.name, "role": rec.role, "mode": rec.mode.value}


@router.post("/run")
async def run(req: RunRequest):
    plan = await coordinator.run(req.agent_id, req.goal, max_iters=req.max_iters)
    return plan.to_dict()


@router.post("/mode")
async def set_mode(req: ModeRequest):
    try:
        mode = AgentMode(req.mode)
    except ValueError:
        raise HTTPException(400, f"invalid mode: {req.mode}")
    coordinator.set_mode(req.agent_id, mode)
    return {"ok": True, "mode": mode.value}


@router.post("/approve")
async def approve(req: ApprovalRequest):
    ok = approval.resolve(req.step_id, req.approved)
    return {"ok": ok}
