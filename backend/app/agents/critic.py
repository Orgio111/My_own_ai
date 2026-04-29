"""Critic: evaluates plan results and may request a re-plan."""
from __future__ import annotations

import json
import re
from typing import Any, Dict

from app.agents.base import Plan
from app.core.orchestrator import orchestrator

CRITIC_SYSTEM = """You are Arajim's CRITIC. Read the goal and the executed plan results.
Decide if the goal is achieved. Output JSON:
{"verdict": "achieved" | "needs_more", "reflection": "...", "next_goal"?: "..."}
"""


def _extract_json(text: str) -> Dict[str, Any]:
    m = re.search(r"\{[\s\S]*\}", text)
    return json.loads(m.group(0)) if m else {"verdict": "achieved", "reflection": text}


async def critique(plan: Plan) -> Dict[str, Any]:
    summary = json.dumps(plan.to_dict(), ensure_ascii=False)[:6000]
    res = await orchestrator.complete(
        [
            {"role": "system", "content": CRITIC_SYSTEM},
            {"role": "user", "content": summary},
        ],
        task_class="reasoning",
        temperature=0.0,
        max_tokens=400,
    )
    try:
        return _extract_json(res["content"])
    except Exception:
        return {"verdict": "achieved", "reflection": res["content"]}
