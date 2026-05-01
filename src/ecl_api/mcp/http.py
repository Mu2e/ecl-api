"""Streamable-HTTP entrypoint — ``ecl-mcp-server`` binds to localhost by default."""

from __future__ import annotations

import argparse
import logging
import os

import uvicorn
from starlette.middleware.cors import CORSMiddleware

from .server import mcp

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(prog="ecl-mcp-server")
    parser.add_argument(
        "--host",
        default=os.environ.get("ECL_MCP_HOST", "127.0.0.1"),
        help="Bind host (default: 127.0.0.1 — localhost only).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("ECL_MCP_PORT", "8766")),
        help="Bind port (default: 8766).",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("ECL_MCP_LOG_LEVEL", "info"),
        help="uvicorn log level.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        log.warning(
            "Binding to %s without authentication. "
            "This exposes ECL credentials and posting capability to anyone who can reach this host.",
            args.host,
        )

    app = mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"],
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
