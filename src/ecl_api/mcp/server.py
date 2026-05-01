"""ecl-api MCP server — FastMCP instance shared by stdio and http transports."""

from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

from .tools import register_all

log = logging.getLogger(__name__)


def _read_only_from_env(default: bool = True) -> bool:
    raw = os.environ.get("ECL_MCP_READ_ONLY")
    if raw is None:
        return default
    return raw.strip().lower() not in ("0", "false", "no", "off")


def build_mcp(name: str = "ecl-mcp", read_only: bool | None = None) -> FastMCP:
    """Build a FastMCP app with all ecl-api tools registered.

    ``read_only`` controls whether destructive tools (post_entry) are
    registered.  ``None`` (default) reads ``ECL_MCP_READ_ONLY`` from the
    environment, defaulting to True (safe).
    """
    if read_only is None:
        read_only = _read_only_from_env()
    mcp = FastMCP(name)
    register_all(mcp, read_only=read_only)
    if not read_only:
        log.warning("ecl-mcp running in WRITE mode — post_entry is enabled.")
    return mcp


mcp = build_mcp()
