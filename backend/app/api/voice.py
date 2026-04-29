"""Voice endpoints — text-in / text-out (browser handles ASR + TTS)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.voice.pipeline import respond

router = APIRouter()


class VoiceRequest(BaseModel):
    text: str


@router.post("/respond")
async def voice_respond(req: VoiceRequest):
    text, lang = await respond(req.text)
    return {"text": text, "lang": lang}
