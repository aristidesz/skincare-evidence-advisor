"""MCP server exposing search_studies, so any MCP host (Claude, Cursor, ...) can call it.

Local, over stdio (the host starts this process):
    uv run python -m src.mcp_server
Remote, over Streamable HTTP at http://HOST:PORT/mcp:
    MCP_TRANSPORT=streamable-http uv run python -m src.mcp_server
"""

import os
from dataclasses import asdict
from typing import Annotated, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from src.tools.studies import SEARCH_STUDIES_TOOL, search_studies

# Reuse the hand-written schema text, so "when to use it" lives in one place.
_SCHEMA = SEARCH_STUDIES_TOOL["function"]
_PARAMS = _SCHEMA["parameters"]["properties"]

mcp = FastMCP(
    "skincare-evidence",
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8000")),
    # No per-client session state: a restarted (or woken-up) server keeps working.
    stateless_http=True,
)


@mcp.tool(name=_SCHEMA["name"], description=_SCHEMA["description"])
def search_studies_tool(
    ingredient: Annotated[str, Field(description=_PARAMS["ingredient"]["description"])],
    concern: Annotated[
        Optional[str], Field(description=_PARAMS["concern"]["description"])
    ] = None,
) -> List[dict]:
    return [asdict(s) for s in search_studies(ingredient, concern)]


if __name__ == "__main__":
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))
