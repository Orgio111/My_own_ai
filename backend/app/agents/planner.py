"""Planner: turns a natural-language goal into a JSON plan."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.agents.base import Plan, Step, new_id
from app.core.orchestrator import orchestrator
from app.utils.logger import log

PLANNER_SYSTEM = """You are Arajim's PLANNER agent. You speak both English and Mongolian fluently.
Decompose the user's goal into a small ordered list of concrete steps that an executor agent can run.

Return ONLY valid JSON of the form:
{
  "summary": "short one-line plan summary",
  "steps": [
    {"description": "...", "tool": "shell.run", "args": {"cmd": "ls"}},
    {"description": "...", "tool": "llm.ask", "args": {"prompt": "..."}}
  ]
}

Available tools:
- "llm.ask"           args: {prompt, task_class?}
- "shell.run"         args: {cmd}
- "filesystem.read"   args: {path}
- "filesystem.write"  args: {path, content}
- "browser.open"      args: {url}
- "browser.read"      args: {selector?}
- "memory.search"     args: {query, k?}
- "memory.write"      args: {key, value}
- "self.read"         args: {path}
- "self.propose"      args: {path, diff}

Keep plans short (<= 8 steps). Be precise. If the goal is just conversational, return a single llm.ask step.
"""


def _extract_json(text: str) -> Dict[str, Any]:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError(f"No JSON in planner output: {text[:200]}")
    return json.loads(m.group(0))


async def plan(goal: str, *, context: str = "") -> Plan:
    msgs: List[Dict[str, Any]] = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": f"GOAL:\n{goal}\n\nCONTEXT:\n{context}"},
    ]
    res = await orchestrator.complete(msgs, task_class="reasoning", temperature=0.2, max_tokens=900)
    try:
        data = _extract_json(res["content"])
    except Exception as e:
        log.warning("planner.parse.fail", err=str(e))
        data = {"summary": "fallback chat", "steps": [{"description": goal, "tool": "llm.ask", "args": {"prompt": goal}}]}

    p = Plan(id=new_id("plan"), goal=goal, summary=data.get("summary", ""))
    for s in data.get("steps", []):
        p.steps.append(
            Step(
                id=new_id("step"),
                description=s.get("description", ""),
                tool=s.get("tool"),
                args=s.get("args", {}) or {},
            )
        )
    return p
