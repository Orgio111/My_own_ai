"""Agent base classes and types."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING = "awaiting_approval"


@dataclass
class Step:
    id: str
    description: str
    tool: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None


@dataclass
class Plan:
    id: str
    goal: str
    steps: List[Step] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "summary": self.summary,
            "steps": [
                {
                    "id": s.id,
                    "description": s.description,
                    "tool": s.tool,
                    "args": s.args,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"
