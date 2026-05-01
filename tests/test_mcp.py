"""Smoke tests for the MCP server — no network or credentials required.

These tests verify wiring (which tools are registered, how the read-only
flag behaves) without ever instantiating an ECL client.  Live integration
tests against a real server live separately and need ECL_* env vars.
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp", reason="mcp extra not installed; run `pip install -e .[mcp]`")

from ecl_api.mcp.server import build_mcp


READ_TOOLS = {
    "search_entries",
    "search_entry_ids",
    "get_entry",
    "list_categories",
    "list_tags",
    "list_forms",
}


def _tool_names(mcp) -> set[str]:
    return {t.name for t in mcp._tool_manager.list_tools()}


def test_read_only_registers_only_read_tools():
    mcp = build_mcp(read_only=True)
    names = _tool_names(mcp)
    assert names == READ_TOOLS


def test_write_mode_adds_post_entry():
    mcp = build_mcp(read_only=False)
    names = _tool_names(mcp)
    assert names == READ_TOOLS | {"post_entry"}


@pytest.mark.parametrize("env_value,expected_read_only", [
    ("true", True),
    ("True", True),
    ("1", True),
    ("yes", True),
    ("false", False),
    ("False", False),
    ("0", False),
    ("no", False),
    ("off", False),
])
def test_read_only_env_var_parsing(monkeypatch, env_value, expected_read_only):
    monkeypatch.setenv("ECL_MCP_READ_ONLY", env_value)
    mcp = build_mcp()
    names = _tool_names(mcp)
    if expected_read_only:
        assert "post_entry" not in names
    else:
        assert "post_entry" in names


def test_read_only_defaults_to_true_when_env_unset(monkeypatch):
    monkeypatch.delenv("ECL_MCP_READ_ONLY", raising=False)
    mcp = build_mcp()
    assert "post_entry" not in _tool_names(mcp)
