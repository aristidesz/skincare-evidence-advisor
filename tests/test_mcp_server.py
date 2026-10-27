import anyio
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
    assert calls == [("retinol", "")]  # only the valid call reached the search
