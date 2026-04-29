"""Example plugin: a fake weather lookup. Replace with a real API."""
from __future__ import annotations

from typing import Awaitable, Callable, Dict

from app.plugins.base import Plugin


async def get_weather(city: str) -> str:
    return f"It's sunny in {city} (stub plugin — wire a real weather API here)."


class WeatherPlugin(Plugin):
    name = "weather"
    version = "0.1.0"

    def tools(self) -> Dict[str, Callable[..., Awaitable]]:
        return {"weather.get": get_weather}
