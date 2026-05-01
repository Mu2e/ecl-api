"""ecl-api MCP server — exposes ECL logbook tools to LLM agents.

v1: read-only by default (search, get, list catalogs).  Posting can be
enabled by setting ``ECL_MCP_READ_ONLY=false`` in the environment, in
which case the ``post_entry`` tool is registered too.

Entrypoints:
- ``ecl-mcp`` / ``ecl-mcp-stdio`` — stdio transport (spawn from an MCP client)
- ``ecl-mcp-server``              — streamable-http, localhost only
"""
