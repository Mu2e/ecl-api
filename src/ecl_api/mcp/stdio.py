"""stdio entrypoint — run ``ecl-mcp-stdio`` as an MCP subprocess."""

from __future__ import annotations

import logging
import os

from .server import mcp


def main() -> None:
    # Log to stderr only — stdout is the MCP transport.
    level_name = os.environ.get("ECL_MCP_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    for noisy in ("mcp", "mcp.server", "mcp.server.lowlevel.server"):
        logging.getLogger(noisy).setLevel(level)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
