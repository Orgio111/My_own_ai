"""Filesystem tool — read/write under a workspace root."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.agents.executor import register_tool

WORKSPACE_ROOT = Path(os.environ.get("ARAJIM_WORKSPACE", os.getcwd())).resolve()


def _resolve(path: str) -> Path:
    p = (WORKSPACE_ROOT / path).resolve() if not os.path.isabs(path) else Path(path).resolve()
    if not str(p).startswith(str(WORKSPACE_ROOT)):
        raise PermissionError(f"path outside workspace: {p}")
    return p


async def read_file(path: str, max_bytes: int = 200_000) -> str:
    p = _resolve(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return p.read_text(encoding="utf-8", errors="replace")[:max_bytes]


async def write_file(path: str, content: str) -> str:
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} bytes to {p}"


async def delete_file(path: str) -> str:
    p = _resolve(path)
    if p.is_dir():
        raise IsADirectoryError(path)
    p.unlink(missing_ok=True)
    return f"deleted {p}"


async def list_dir(path: str = ".", glob: Optional[str] = None) -> list[str]:
    p = _resolve(path)
    if not p.is_dir():
        raise NotADirectoryError(path)
    items = sorted(p.glob(glob) if glob else p.iterdir())
    return [str(i.relative_to(WORKSPACE_ROOT)) for i in items]


register_tool("filesystem.read", read_file)
register_tool("filesystem.write", write_file)
register_tool("filesystem.delete", delete_file)
register_tool("filesystem.list", list_dir)
