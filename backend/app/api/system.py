"""System metrics + model registry endpoints."""
from __future__ import annotations

import time

import psutil
from fastapi import APIRouter

from app.core.router import list_models
from app.core.token_tracker import tracker

router = APIRouter()
_BOOT = time.time()


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
    return list_models()


@router.get("/usage")
async def usage():
    return tracker.snapshot()
