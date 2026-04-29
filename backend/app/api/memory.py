"""Memory API: search, upsert, session history."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.memory.store import store
from app.memory.summarizer import summarize

router = APIRouter()


class UpsertRequest(BaseModel):
    key: Optional[str] = None
    value: str
    metadata: Optional[Dict[str, Any]] = None


class SummarizeRequest(BaseModel):
    session_id: str


@router.post("/upsert")
async def upsert(req: UpsertRequest):
    rid = await store.upsert(req.key, req.value, req.metadata)
    return {"id": rid}


@router.get("/search")
async def search(q: str, k: int = 5):
    return await store.search(q, k=k)


@router.get("/session/{session_id}")
async def session(session_id: str, limit: int = 50):
    return await store.session_history(session_id, limit=limit)


@router.post("/summarize")
async def summarize_endpoint(req: SummarizeRequest):
    history = await store.session_history(req.session_id, limit=200)
    text = await summarize(history)
    rid = await store.upsert(f"summary:{req.session_id}", text, {"session_id": req.session_id})
    return {"id": rid, "summary": text}
