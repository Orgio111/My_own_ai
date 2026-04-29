"""Self-improvement primitives — guarded by SELF_MODIFY_ENABLED."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict

from app.agents.executor import register_tool
from app.config import settings

REPO_ROOT = Path(__file__).resolve().parents[3]


def _ensure_enabled() -> None:
    if not settings.self_modify_enabled:
        raise RuntimeError("self-modify is disabled (set SELF_MODIFY_ENABLED=true to enable)")


async def read_self(path: str) -> str:
    p = (REPO_ROOT / path).resolve()
    if not str(p).startswith(str(REPO_ROOT)):
        raise PermissionError("escape attempt")
    return p.read_text(encoding="utf-8", errors="replace")[:200_000]


async def propose_patch(path: str, diff: str) -> Dict[str, str]:
    """Write `diff` (unified) to a sandbox branch via git apply."""
    _ensure_enabled()
    branch = settings.self_modify_branch
    subprocess.run(["git", "checkout", "-B", branch], cwd=REPO_ROOT, check=True)
    proc = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=REPO_ROOT,
        input=diff.encode("utf-8"),
        capture_output=True,
    )
    if proc.returncode != 0:
        return {"ok": "false", "error": proc.stderr.decode()}
    subprocess.run(
        ["git", "apply", "-"], cwd=REPO_ROOT, input=diff.encode("utf-8"), check=True
    )
    subprocess.run(["git", "add", path], cwd=REPO_ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"arajim: self-improve {path}"],
        cwd=REPO_ROOT,
        check=True,
    )
    return {"ok": "true", "branch": branch}


async def run_tests() -> Dict[str, str]:
    _ensure_enabled()
    proc = subprocess.run(
        ["python", "-m", "pytest", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    return {
        "exit": str(proc.returncode),
        "stdout": proc.stdout.decode()[:10_000],
        "stderr": proc.stderr.decode()[:10_000],
    }


register_tool("self.read", read_self)
register_tool("self.propose", propose_patch)
register_tool("self.test", run_tests)
