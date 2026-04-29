"""Plugin ABC.

Drop a Python file in app/plugins/contrib/ that exports a subclass of Plugin.
The loader will auto-discover, instantiate, and register its tools.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Dict, List


class Plugin(ABC):
    name: str = "unnamed"
    version: str = "0.1.0"

    @abstractmethod
    def tools(self) -> Dict[str, Callable[..., Awaitable]]:
        """Map of tool_name -> async callable."""
        ...

    def on_load(self) -> None:
        """Optional hook."""
