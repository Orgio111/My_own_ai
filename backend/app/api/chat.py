"""Chat API — synchronous + streaming."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.core.orchestrator import orchestrator
from app.memory.store import store

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    task_class: str = "reasoning"
    model: Optional[str] = None
    temperature: float = 0.4
    max_tokens: int = 1024
    session_id: Optional[str] = None


@router.post("")
async def chat(req: ChatRequest):
    msgs = [m.model_dump() for m in req.messages]
    res = await orchestrator.complete(
        msgs,
        task_class=req.task_class,
        model_override=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    if req.session_id:
        last_user = next((m for m in reversed(msgs) if m["role"] == "user"), None)
        if last_user:
            await store.append_session(req.session_id, "user", last_user["content"])
        await store.append_session(req.session_id, "assistant", res["content"])
    return res


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    msgs = [m.model_dump() for m in req.messages]

    async def gen():
        full = []
        async for tok in orchestrator.stream(
            msgs,
            task_class=req.task_class,
            model_override=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        ):
            full.append(tok)
            yield {"event": "token", "data": tok}
        if req.session_id:
            last_user = next((m for m in reversed(msgs) if m["role"] == "user"), None)
            if last_user:
                await store.append_session(req.session_id, "user", last_user["content"])
            await store.append_session(req.session_id, "assistant", "".join(full))
        yield {"event": "done", "data": ""}

    return EventSourceResponse(gen())
