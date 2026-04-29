"""Embedding helper using NVIDIA embed model with a simple in-memory cache."""
from __future__ import annotations

import hashlib
from typing import Dict, List

from app.config import settings
from app.core.nvidia_client import nvidia

_cache: Dict[str, List[float]] = {}


def _key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def embed(texts: List[str]) -> List[List[float]]:
    out: List[List[float]] = []
    needed: List[str] = []
    needed_idx: List[int] = []
    for i, t in enumerate(texts):
        c = _cache.get(_key(t))
        if c is None:
            needed_idx.append(i)
            needed.append(t)
            out.append([])
        else:
            out.append(c)
    if needed:
        try:
            vecs = await nvidia.embed(settings.model_embed, needed)
        except Exception:
            # graceful fallback: deterministic fake vectors so the system still runs offline
            vecs = [_fake_vec(t) for t in needed]
        for i, v in zip(needed_idx, vecs):
            out[i] = v
            _cache[_key(texts[i])] = v
    return out


def _fake_vec(text: str, dim: int = 64) -> List[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    return [(b / 255.0) * 2 - 1 for b in (h * ((dim // len(h)) + 1))[:dim]]
