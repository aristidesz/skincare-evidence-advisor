"""MCP server exposing search_studies, so any MCP host (Claude, Cursor, ...) can call it.

Serves Streamable HTTP at http://0.0.0.0:7860/mcp (on Render, render.yaml sets PORT=7860 to match):
    uv run python -m src.mcp_server
"""

import threading
import time
from collections import deque
from datetime import datetime, timezone
from functools import lru_cache
from typing import Annotated, Callable, Deque, List, Optional, Tuple

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from src.tools.studies import (
    SEARCH_STUDIES_TOOL,
    Study,
    StudySearchError,
    search_studies,
)

# Reuse the hand-written schema text, so "when to use it" lives in one place.
_SCHEMA = SEARCH_STUDIES_TOOL["function"]
_PARAMS = _SCHEMA["parameters"]["properties"]

# The endpoint is public: reject oversized input before it reaches Europe PMC.
# Generous on purpose: "Bis-Ethylhexyloxyphenol Methoxyphenyl Triazine" is 46 characters.
MAX_INPUT_CHARS = 80

mcp = MCPServer("skincare-evidence")


class _RateLimit:
    """At most `max_calls` per `per_seconds`, counted across all callers (a sliding window)."""

    def __init__(
        self,
        max_calls: int,
        per_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_calls = max_calls
        self._per_seconds = per_seconds
        self._clock = clock
        self._calls: Deque[float] = deque()
        self._lock = threading.Lock()  # the SDK runs the tool in worker threads

    def allow(self) -> bool:
        now = self._clock()
        with self._lock:
            while self._calls and now - self._calls[0] >= self._per_seconds:
                self._calls.popleft()
            if len(self._calls) >= self._max_calls:
                return False
            self._calls.append(now)
            return True


# New (uncached) Europe PMC searches. My own conservative choice: Europe PMC publishes no
# number, and EMBL-EBI's terms only say use that stops it serving others gets you blocked.
# ponytail: one global budget, so one caller can use it all for a minute (cached questions
# still work); a per-caller limit needs the caller's address from Render's forwarding header.
_searches = _RateLimit(max_calls=30, per_seconds=60)


def _quarter() -> str:
    """The calendar quarter (UTC), such as "2026-Q4"."""
    now = datetime.now(timezone.utc)
    return f"{now.year}-Q{(now.month - 1) // 3 + 1}"


# Repeated questions skip Europe PMC. In memory only, so it empties when the free
# Render service sleeps or redeploys. lru_cache never stores an exception, so a
# failed or refused search is simply tried again. `quarter` is only here to be part
# of the key: an entry is never reused in a later quarter, so results are refreshed.
# The rate limit sits inside the cache, so only real Europe PMC calls use a slot.
# ponytail: no per-entry clock or byte limit; add a TTL if staleness or memory matters.
@lru_cache(maxsize=256)
def _cached_search(
    ingredient: str, concern: Optional[str], quarter: str
) -> Tuple[Study, ...]:
    if not _searches.allow():  # a failed attempt still counts: it still hit Europe PMC
        raise ToolError("Too many searches right now. Try again in a minute.")
    return tuple(search_studies(ingredient, concern))


# A plain def on purpose: mcp 2.x runs sync tools in a worker thread, so the
# blocking Europe PMC call does not stall other clients on the event loop.
@mcp.tool(name=_SCHEMA["name"], description=_SCHEMA["description"])
def search_studies_tool(
    ingredient: Annotated[
        str,
        Field(
            description=_PARAMS["ingredient"]["description"],
            min_length=2,
            max_length=MAX_INPUT_CHARS,
        ),
    ],
    concern: Annotated[
        Optional[str],
        Field(
            description=_PARAMS["concern"]["description"], max_length=MAX_INPUT_CHARS
        ),
    ] = None,
) -> List[Study]:
    # Normalise first, so "Niacinamide " and "niacinamide" share one cache entry.
    ingredient = ingredient.strip().lower()
    concern = (concern or "").strip().lower() or None
    try:
        return list(_cached_search(ingredient, concern, _quarter()))
    except StudySearchError as error:
        # A ToolError keeps its message for the caller; any other exception would
        # reach them as just "Error executing tool search_studies".
        raise ToolError(str(error)) from error


if __name__ == "__main__":
    # Stateless: no per-client sessions, so a restarted (or woken-up) server keeps working.
    mcp.run("streamable-http", host="0.0.0.0", port=7860, stateless_http=True)
