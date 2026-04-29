"""Agent execution modes — auto / guided / manual."""
from __future__ import annotations

from enum import Enum


class AgentMode(str, Enum):
    AUTO = "auto"        # execute everything, including risky actions
    GUIDED = "guided"    # ask for approval on risky actions (default)
    MANUAL = "manual"    # user runs every step explicitly


RISKY_TOOLS = {"shell.run", "filesystem.write", "filesystem.delete", "self.apply", "browser.submit"}


def is_risky(tool_name: str) -> bool:
    return tool_name in RISKY_TOOLS


def requires_approval(mode: AgentMode, tool_name: str) -> bool:
    if mode == AgentMode.AUTO:
        return False
    if mode == AgentMode.MANUAL:
        return True
    return is_risky(tool_name)
