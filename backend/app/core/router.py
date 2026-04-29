"""Model router — picks the best NVIDIA model for a given task class."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.config import settings


@dataclass
class ModelCard:
    id: str
    role: str            # "reasoning" | "code" | "fast" | "vision" | "embed"
    ctx: int
    strengths: List[str] = field(default_factory=list)
    healthy: bool = True


REGISTRY: Dict[str, ModelCard] = {
    settings.model_reasoning: ModelCard(
        id=settings.model_reasoning,
        role="reasoning",
        ctx=128_000,
        strengths=["planning", "analysis", "long-form", "tool-use"],
    ),
    settings.model_fast: ModelCard(
        id=settings.model_fast,
        role="fast",
        ctx=128_000,
        strengths=["chat", "small-tasks", "low-latency"],
    ),
    settings.model_code: ModelCard(
        id=settings.model_code,
        role="code",
        ctx=128_000,
        strengths=["code", "refactor", "debug"],
    ),
    settings.model_vision: ModelCard(
        id=settings.model_vision,
        role="vision",
        ctx=128_000,
        strengths=["image", "screenshot", "diagram"],
    ),
    settings.model_embed: ModelCard(
        id=settings.model_embed,
        role="embed",
        ctx=512,
        strengths=["semantic-search"],
    ),
}


def pick(task_class: str = "reasoning", *, override: Optional[str] = None) -> ModelCard:
    """Pick a model. If `override` is supplied it is honoured even when not in REGISTRY
    (so the user can select any NVIDIA-hosted model from the live catalog)."""
    if override:
        if override in REGISTRY:
            return REGISTRY[override]
        # synthetic card for an unknown but explicitly requested model
        card = ModelCard(id=override, role=_infer_role(override), ctx=128_000, strengths=["user-selected"])
        REGISTRY[override] = card
        return card
    for card in REGISTRY.values():
        if card.role == task_class and card.healthy:
            return card
    return REGISTRY[settings.model_reasoning]


def _infer_role(model_id: str) -> str:
    m = model_id.lower()
    if "embed" in m:
        return "embed"
    if "vision" in m or "vl" in m:
        return "vision"
    if "code" in m or "coder" in m:
        return "code"
    if any(t in m for t in ("8b", "mini", "small", "fast", "haiku")):
        return "fast"
    return "reasoning"


def upsert(card: ModelCard) -> None:
    REGISTRY[card.id] = card


def mark_unhealthy(model_id: str) -> None:
    if model_id in REGISTRY:
        REGISTRY[model_id].healthy = False


def mark_healthy(model_id: str) -> None:
    if model_id in REGISTRY:
        REGISTRY[model_id].healthy = True


def list_models() -> List[Dict]:
    return [card.__dict__ for card in REGISTRY.values()]
