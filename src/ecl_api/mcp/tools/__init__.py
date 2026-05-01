"""MCP tool registration.

Each submodule defines one or more functions and a ``register(mcp)``
hook.  ``register_all`` calls every read tool's hook, plus ``post.register``
when ``read_only=False``.
"""

from __future__ import annotations

from . import entries, metadata


def register_all(mcp, read_only: bool = True) -> None:
    """Register every ecl-api MCP tool with the given FastMCP instance."""
    entries.register(mcp)
    metadata.register(mcp)
    if not read_only:
        from . import post  # noqa: PLC0415  (only import write path when enabled)
        post.register(mcp)
