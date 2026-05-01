"""Shared ECL client for the MCP server.

A single :class:`ecl_api.ECL` instance is cached per-process.  Constructed
lazily on first tool call from ``ECL_URL``, ``ECL_USER_NAME``, and
``ECL_PASSWORD`` environment variables.  Always uses ``as_json=True`` so
tools return JSON-friendly Python objects.

Caching the instance preserves the metadata cache (categories/tags/forms)
across tool calls and avoids re-running the active-server probe on every
request.
"""

from __future__ import annotations

import threading

from ecl_api import ECL

_lock = threading.Lock()
_instance: ECL | None = None


def get_ecl() -> ECL:
    """Return the process-wide ECL client, constructing it on first call."""
    global _instance
    with _lock:
        if _instance is None:
            _instance = ECL(as_json=True)
        return _instance


def reset_ecl() -> None:
    """Drop the cached client (e.g. after a credential rotation)."""
    global _instance
    with _lock:
        _instance = None
