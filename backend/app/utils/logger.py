"""Structured logger; emits JSON in prod, pretty in dev."""
from __future__ import annotations

import logging
import sys

import structlog

from app.config import settings


def _configure() -> structlog.stdlib.BoundLogger:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if settings.debug:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())
    structlog.configure(processors=processors)
    return structlog.get_logger("arajim")


log = _configure()
