"""Async NVIDIA AI API client.

Uses the OpenAI-compatible REST surface at integrate.api.nvidia.com.
Supports chat (sync + streaming) and embeddings.
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.utils.logger import log


class NvidiaError(RuntimeError):
    pass


class NvidiaClient:
    def __init__(self, api_key: Optional[str] = None, base: Optional[str] = None) -> None:
        self.api_key = api_key or settings.nvidia_api_key
        self.base = (base or settings.nvidia_api_base).rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=180.0))

    async def aclose(self) -> None:
        await self._client.aclose()

    @property
    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise NvidiaError("NVIDIA_API_KEY not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: float = 0.4,
        top_p: float = 0.95,
        max_tokens: int = 1024,
        tools: Optional[List[Dict[str, Any]]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        if extra:
            payload.update(extra)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(httpx.TransportError),
            reraise=True,
        ):
            with attempt:
                r = await self._client.post(
                    f"{self.base}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                if r.status_code >= 400:
                    log.error("nvidia.chat.error", status=r.status_code, body=r.text[:400])
                    raise NvidiaError(f"chat {r.status_code}: {r.text[:400]}")
                return r.json()
        raise NvidiaError("unreachable")

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with self._client.stream(
            "POST", f"{self.base}/chat/completions", headers=self._headers, json=payload
        ) as r:
            if r.status_code >= 400:
                body = await r.aread()
                raise NvidiaError(f"stream {r.status_code}: {body[:400]!r}")
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    return
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = obj.get("choices", [{}])[0].get("delta", {})
                token = delta.get("content")
                if token:
                    yield token

    async def list_models(self) -> List[Dict[str, Any]]:
        """Fetch the live NVIDIA model catalog (OpenAI-compatible /models endpoint)."""
        r = await self._client.get(f"{self.base}/models", headers=self._headers)
        if r.status_code >= 400:
            raise NvidiaError(f"models {r.status_code}: {r.text[:400]}")
        data = r.json()
        return data.get("data", data) if isinstance(data, dict) else data

    async def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        r = await self._client.post(
            f"{self.base}/embeddings",
            headers=self._headers,
            json={"model": model, "input": texts, "input_type": "query"},
        )
        if r.status_code >= 400:
            raise NvidiaError(f"embed {r.status_code}: {r.text[:400]}")
        data = r.json()["data"]
        return [d["embedding"] for d in data]


nvidia = NvidiaClient()
