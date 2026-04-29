"""Hybrid memory store: SQLite for episodic + numpy cosine vector index."""
from __future__ import annotations

import asyncio
import json
import math
import time
from typing import Any, Dict, List, Optional

import aiosqlite

from app.config import settings
from app.memory.embeddings import embed


class MemoryStore:
    def __init__(self, path: str = settings.sqlite_path) -> None:
        self.path = path
        self._lock = asyncio.Lock()
        self._ready = False

    async def _init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    value TEXT NOT NULL,
                    embedding TEXT,
                    metadata TEXT,
                    created_at REAL NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            await db.commit()
        self._ready = True

    async def _ensure(self) -> None:
        if not self._ready:
            async with self._lock:
                if not self._ready:
                    await self._init()

    async def upsert(self, key: Optional[str], value: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        await self._ensure()
        vec = (await embed([value]))[0]
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "INSERT INTO memories (key,value,embedding,metadata,created_at) VALUES (?,?,?,?,?)",
                (key, value, json.dumps(vec), json.dumps(metadata or {}), time.time()),
            )
            await db.commit()
            return cur.lastrowid or 0

    async def append_session(self, session_id: str, role: str, content: str) -> None:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO sessions (id,role,content,created_at) VALUES (?,?,?,?)",
                (session_id, role, content, time.time()),
            )
            await db.commit()

    async def session_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        await self._ensure()
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT role,content,created_at FROM sessions WHERE id=? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ) as cur:
                rows = await cur.fetchall()
        rows.reverse()
        return [{"role": r, "content": c, "ts": t} for r, c, t in rows]

    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        await self._ensure()
        qvec = (await embed([query]))[0]
        async with aiosqlite.connect(self.path) as db:
            async with db.execute(
                "SELECT id,key,value,embedding,metadata,created_at FROM memories"
            ) as cur:
                rows = await cur.fetchall()
        scored = []
        for id_, key, val, emb_json, meta_json, ts in rows:
            try:
                v = json.loads(emb_json) if emb_json else None
            except Exception:
                continue
            if not v:
                continue
            scored.append((_cos(qvec, v), {
                "id": id_, "key": key, "value": val,
                "metadata": json.loads(meta_json or "{}"),
                "created_at": ts,
            }))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, **m} for s, m in scored[:k]]


def _cos(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


store = MemoryStore()
