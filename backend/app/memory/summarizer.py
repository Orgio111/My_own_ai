"""Conversation summarizer for long-context compression."""
from __future__ import annotations

from typing import Dict, List

from app.core.orchestrator import orchestrator

SUMMARY_SYSTEM = """Summarize this conversation segment into a concise memory card.
Preserve user preferences, names, decisions, and any unfinished tasks.
Output 5-8 short bullet points. Match the user's language (English / Mongolian)."""


async def summarize(messages: List[Dict[str, str]]) -> str:
    transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    res = await orchestrator.complete(
        [
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": transcript[:8000]},
        ],
        task_class="fast",
        max_tokens=400,
    )
    return res["content"]
