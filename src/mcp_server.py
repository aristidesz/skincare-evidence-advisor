"""MCP server exposing search_studies, so any MCP host (Claude, Cursor, ...) can call it.

Serves Streamable HTTP at http://0.0.0.0:7860/mcp (on Render, render.yaml sets PORT=7860 to match):
    uv run python -m src.mcp_server
"""

from typing import Annotated, List, Optional

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from src.tools.studies import SEARCH_STUDIES_TOOL, Study, search_studies

# Reuse the hand-written schema text, so "when to use it" lives in one place.
_SCHEMA = SEARCH_STUDIES_TOOL["function"]
_PARAMS = _SCHEMA["parameters"]["properties"]

mcp = MCPServer("skincare-evidence")


# A plain def on purpose: mcp 2.x runs sync tools in a worker thread, so the
# blocking Europe PMC call does not stall other clients on the event loop.
@mcp.tool(name=_SCHEMA["name"], description=_SCHEMA["description"])
def search_studies_tool(
    ingredient: Annotated[str, Field(description=_PARAMS["ingredient"]["description"])],
    concern: Annotated[
        Optional[str], Field(description=_PARAMS["concern"]["description"])
    ] = None,
) -> List[Study]:
    return search_studies(ingredient, concern)


if __name__ == "__main__":
    # Stateless: no per-client sessions, so a restarted (or woken-up) server keeps working.
    mcp.run("streamable-http", host="0.0.0.0", port=7860, stateless_http=True)
