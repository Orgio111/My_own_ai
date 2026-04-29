"""Voice pipeline.

The browser does ASR/TTS by default (free, fast, supports mn-MN + en-US).
Server-side endpoints below are stubs that can be wired to NVIDIA Riva.
"""
from __future__ import annotations

import re
from typing import Tuple

from app.core.orchestrator import orchestrator

VOICE_SYSTEM = """You are Arajim, a voice assistant. Be concise; reply in the user's language.
If the user spoke Mongolian (Cyrillic), reply in Mongolian. Otherwise reply in English."""


def detect_language(text: str) -> str:
    return "mn-MN" if re.search(r"[Ѐ-ӿ]", text) else "en-US"


async def respond(text: str) -> Tuple[str, str]:
    """Returns (assistant_text, language_tag)."""
    lang = detect_language(text)
    res = await orchestrator.complete(
        [
            {"role": "system", "content": VOICE_SYSTEM},
            {"role": "user", "content": text},
        ],
        task_class="fast",
        max_tokens=400,
        temperature=0.5,
    )
    return res["content"], lang
