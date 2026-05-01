"""Shared helpers for tool modules."""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable

log = logging.getLogger(__name__)


def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Convert exceptions raised inside a tool into structured error dicts.

    Keeps the agent-facing contract simple: every tool either returns its
    normal payload or ``{"error": "<code>", "message": "<detail>"}``.
    """

    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            return {"error": "bad_request", "message": str(e)}
        except Exception as e:
            log.exception("MCP tool %s failed", fn.__name__)
            return {"error": "tool_failed", "message": f"{type(e).__name__}: {e}"}

    return inner
