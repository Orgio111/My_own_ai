"""Shell tool — runs commands restricted to an allow-list of binaries."""
from __future__ import annotations

import asyncio
import shlex
from typing import Dict

from app.agents.executor import register_tool
from app.config import settings


class ShellError(RuntimeError):
    pass


def _check(cmd: str) -> str:
    parts = shlex.split(cmd)
    if not parts:
        raise ShellError("empty command")
    bin_name = parts[0].split("/")[-1]
    allowed = settings.shell_allowed_list
    if bin_name not in allowed:
        raise ShellError(f"binary not allowed: {bin_name}. allow-list: {allowed}")
    return cmd


async def run(cmd: str, timeout: float = 60.0) -> Dict[str, str]:
    safe = _check(cmd)
    proc = await asyncio.create_subprocess_shell(
        safe,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise ShellError(f"timeout after {timeout}s")
    return {
        "exit": proc.returncode or 0,
        "stdout": stdout.decode("utf-8", errors="replace")[:20_000],
        "stderr": stderr.decode("utf-8", errors="replace")[:20_000],
    }


register_tool("shell.run", run)
