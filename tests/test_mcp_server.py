from datetime import datetime

import anyio
import pytest
from mcp import Client

import src.mcp_server as server
from src.tools.studies import Study, StudySearchError

STUDY = Study(
    title="Topical niacinamide for acne: a randomized trial.",
    authors="Smith A, Jones B.",
    journal="J Dermatol",
    year=2021,
    study_type="randomized controlled trial",
    abstract="Niacinamide reduced lesions.",
    url="https://pubmed.ncbi.nlm.nih.gov/11111111/",
    pmid="11111111",
    open_access=True,
    cited_by=12,
)


@pytest.fixture(autouse=True)
def _fresh_state(monkeypatch):
    # The cache and the rate limit are module-level: start every test with neither used.
    server._cached_search.cache_clear()
    monkeypatch.setattr(server, "_searches", server._RateLimit(30, 60))


def _ask(*arguments):
    """Call search_studies once per argument dict, in memory, and return the results."""

    async def run():
        async with Client(server.mcp) as client:
            return [await client.call_tool("search_studies", a) for a in arguments]

    return anyio.run(run)


def test_mcp_server_lists_and_calls_search_studies(monkeypatch):
    calls = []

    def fake_search(ingredient, concern=None):
        calls.append((ingredient, concern))
        return [STUDY]

    # The Europe PMC call itself is covered in tests/tools/test_studies.py.
    monkeypatch.setattr(server, "search_studies", fake_search)

    async def run():
        # In memory: real MCP messages (initialize, tools/list, tools/call), no network.
        async with Client(server.mcp) as client:
            tools = (await client.list_tools()).tools
            result = await client.call_tool(
                "search_studies", {"ingredient": "niacinamide", "concern": "acne"}
            )
            return tools, result

    tools, result = anyio.run(run)

    assert [t.name for t in tools] == ["search_studies"]
    assert tools[0].input_schema["required"] == ["ingredient"]
    assert "when the user asks" in tools[0].description
    assert tools[0].output_schema is not None
    assert not result.is_error
    assert calls == [("niacinamide", "acne")]
    assert result.structured_content["result"][0]["pmid"] == "11111111"


def test_mcp_server_tells_the_caller_why_a_search_failed(monkeypatch):
    def failing_search(ingredient, concern=None):
        raise StudySearchError("Europe PMC is temporarily unavailable. Try again.")

    monkeypatch.setattr(server, "search_studies", failing_search)

    async def run():
        async with Client(server.mcp) as client:
            return await client.call_tool("search_studies", {"ingredient": "retinol"})

    result = anyio.run(run)

    assert result.is_error
    assert "temporarily unavailable" in result.content[0].text


def test_mcp_server_rejects_oversized_input_before_searching(monkeypatch):
    calls = []
    monkeypatch.setattr(
        server, "search_studies", lambda *args: calls.append(args) or [STUDY]
    )
    too_long = "x" * (server.MAX_INPUT_CHARS + 1)

    async def run():
        async with Client(server.mcp) as client:
            props = (await client.list_tools()).tools[0].input_schema["properties"]
            rejected = [
                await client.call_tool("search_studies", args)
                for args in (
                    {"ingredient": "a"},
                    {"ingredient": too_long},
                    {"ingredient": "retinol", "concern": too_long},
                )
            ]
            allowed = await client.call_tool(
                "search_studies", {"ingredient": "retinol", "concern": ""}
            )
            return props, rejected, allowed

    props, rejected, allowed = anyio.run(run)

    assert props["ingredient"]["minLength"] == 2
    assert props["ingredient"]["maxLength"] == server.MAX_INPUT_CHARS
    assert all(result.is_error for result in rejected)
    assert not allowed.is_error
    assert calls == [("retinol", None)]  # only the valid call reached the search


def test_repeated_searches_are_answered_from_the_cache(monkeypatch):
    calls = []
    monkeypatch.setattr(
        server, "search_studies", lambda *args: calls.append(args) or [STUDY]
    )

    results = _ask(
        {"ingredient": "niacinamide", "concern": "acne"},
        {"ingredient": "  Niacinamide ", "concern": "ACNE"},  # same after tidying up
        {"ingredient": "niacinamide"},  # no concern: a different question
    )

    assert not any(result.is_error for result in results)
    assert calls == [("niacinamide", "acne"), ("niacinamide", None)]
    assert results[0].structured_content == results[1].structured_content


def test_a_failed_search_is_not_cached(monkeypatch):
    calls = []

    def flaky_search(ingredient, concern=None):
        calls.append(ingredient)
        if len(calls) == 1:
            raise StudySearchError("Europe PMC is temporarily unavailable.")
        return [STUDY]

    monkeypatch.setattr(server, "search_studies", flaky_search)

    first, second, third = _ask(*[{"ingredient": "retinol"}] * 3)

    assert first.is_error
    assert not second.is_error and not third.is_error
    assert len(calls) == 2  # the failure was retried, then the success was remembered


def test_the_cache_is_refreshed_each_quarter(monkeypatch):
    calls = []
    monkeypatch.setattr(
        server, "search_studies", lambda *args: calls.append(args) or [STUDY]
    )
    quarter = {"now": "2026-Q4"}
    monkeypatch.setattr(server, "_quarter", lambda: quarter["now"])

    _ask({"ingredient": "retinol"}, {"ingredient": "retinol"})
    quarter["now"] = "2027-Q1"
    _ask({"ingredient": "retinol"})

    assert len(calls) == 2


@pytest.mark.parametrize(
    "month, expected",
    [
        (1, "Q1"),
        (3, "Q1"),
        (4, "Q2"),
        (6, "Q2"),
        (7, "Q3"),
        (9, "Q3"),
        (10, "Q4"),
        (12, "Q4"),
    ],
)
def test_quarter_is_the_calendar_quarter(monkeypatch, month, expected):
    class FakeDatetime:
        @staticmethod
        def now(tz=None):
            return datetime(2026, month, 15, tzinfo=tz)

    monkeypatch.setattr(server, "datetime", FakeDatetime)

    assert server._quarter() == f"2026-{expected}"


def test_rate_limit_allows_a_burst_then_refuses_until_the_window_slides():
    now = {"t": 0.0}
    limit = server._RateLimit(2, 60, clock=lambda: now["t"])

    assert [limit.allow(), limit.allow(), limit.allow()] == [True, True, False]
    now["t"] = 59.9
    assert limit.allow() is False
    now["t"] = 60.0
    assert limit.allow() is True  # the first two calls have left the window


def test_only_new_searches_use_the_rate_limit_and_a_refusal_is_not_cached(monkeypatch):
    now = {"t": 0.0}
    monkeypatch.setattr(
        server, "_searches", server._RateLimit(2, 60, clock=lambda: now["t"])
    )
    calls = []
    monkeypatch.setattr(
        server, "search_studies", lambda *args: calls.append(args) or [STUDY]
    )

    first, repeat, second, refused = _ask(
        {"ingredient": "retinol"},
        {"ingredient": "retinol"},  # remembered, so it uses no slot
        {"ingredient": "niacinamide"},
        {"ingredient": "vitamin c"},  # a third new question: over the limit
    )

    assert [r.is_error for r in (first, repeat, second, refused)] == [
        False,
        False,
        False,
        True,
    ]
    assert "Too many searches" in refused.content[0].text
    assert len(calls) == 2  # the refused question never reached Europe PMC

    now["t"] = 60.0
    (retried,) = _ask({"ingredient": "vitamin c"})
    assert not retried.is_error  # the refusal was not remembered
    assert len(calls) == 3
