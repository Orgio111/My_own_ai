"""Single WebSocket gateway: streams events + accepts commands."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.coordinator import coordinator
from app.agents.executor import approval
from app.agents.modes import AgentMode
from app.utils.events import bus
from app.utils.logger import log

# eager-import tools + plugins so registry is populated
from app.tools import filesystem, shell, browser, self_modify, memory_tool  # noqa: F401
from app.plugins.loader import discover  # noqa: F401

discover()

router = APIRouter()


@router.websocket("/ws")
async def gateway(ws: WebSocket) -> None:
    await ws.accept()
    log.info("ws.connect")
    queue = bus.subscribe("*")

    async def pump_out():
        while True:
            msg = await queue.get()
            await ws.send_text(json.dumps(msg, default=str))

    out_task = asyncio.create_task(pump_out())
    try:
        while True:
            raw = await ws.receive_text()
            try:
                cmd = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"topic": "error", "msg": "invalid json"}))
                continue
            await _handle(cmd, ws)
    except WebSocketDisconnect:
        log.info("ws.disconnect")
    finally:
        out_task.cancel()
        bus.unsubscribe("*", queue)


async def _handle(cmd: dict, ws: WebSocket) -> None:
    op = cmd.get("op")
    if op == "agent.spawn":
        rec = coordinator.spawn(
            name=cmd.get("name", "agent"),
            role=cmd.get("role", "general"),
            mode=AgentMode(cmd["mode"]) if cmd.get("mode") else None,
        )
        await ws.send_text(json.dumps({"topic": "agent.spawned", "agent": {"id": rec.id, "name": rec.name}}))
    elif op == "agent.run":
        agent_id = cmd["agent_id"]
        goal = cmd["goal"]
        asyncio.create_task(coordinator.run(agent_id, goal))
        await ws.send_text(json.dumps({"topic": "agent.run.queued", "agent_id": agent_id}))
    elif op == "agent.mode":
        coordinator.set_mode(cmd["agent_id"], AgentMode(cmd["mode"]))
        await ws.send_text(json.dumps({"topic": "agent.mode.set", "agent_id": cmd["agent_id"]}))
    elif op == "approval":
        approval.resolve(cmd["step_id"], bool(cmd.get("approved", False)))
    elif op == "ping":
        await ws.send_text(json.dumps({"topic": "pong"}))
    else:
        await ws.send_text(json.dumps({"topic": "error", "msg": f"unknown op: {op}"}))
