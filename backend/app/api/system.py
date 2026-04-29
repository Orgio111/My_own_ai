"""System metrics + model registry endpoints."""
from __future__ import annotations

import time
from typing import Any, Dict, List

import psutil
from fastapi import APIRouter

from app.core.nvidia_client import NvidiaError, nvidia
from app.core.router import _infer_role, list_models
from app.core.token_tracker import tracker
from app.utils.logger import log

router = APIRouter()
_BOOT = time.time()

_NVIDIA_CACHE: Dict[str, Any] = {"ts": 0.0, "models": []}
_NVIDIA_TTL = 300  # 5 min


@router.get("/health")
async def health():
    return {
        "status": "alive",
        "uptime_sec": int(time.time() - _BOOT),
        "cpu": psutil.cpu_percent(interval=None),
        "mem": psutil.virtual_memory().percent,
    }


@router.get("/models")
async def models():
    """Locally-registered models (fast, used by router)."""
    return list_models()


@router.get("/models/available")
async def available_models(refresh: bool = False) -> List[Dict[str, Any]]:
    """Live NVIDIA catalog. Cached for 5 minutes; pass ?refresh=true to force."""
    now = time.time()
    if not refresh and _NVIDIA_CACHE["models"] and now - _NVIDIA_CACHE["ts"] < _NVIDIA_TTL:
        return _NVIDIA_CACHE["models"]
    try:
        raw = await nvidia.list_models()
    except NvidiaError as e:
        log.warning("system.models.available.fallback", err=str(e))
        return list_models()
    out: List[Dict[str, Any]] = []
    for m in raw:
        mid = m.get("id") or m.get("name")
        if not mid:
            continue
        out.append({
            "id": mid,
            "role": _infer_role(mid),
            "owned_by": m.get("owned_by", ""),
            "created": m.get("created"),
        })
    out.sort(key=lambda x: (x["role"], x["id"]))
    _NVIDIA_CACHE["ts"] = now
    _NVIDIA_CACHE["models"] = out
    return out


@router.get("/usage")
async def usage():
    return tracker.snapshot()
