import anyio
from mcp.shared.memory import create_connected_server_and_client_session

import src.mcp_server as server
from src.tools.studies import Study

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
        async with create_connected_server_and_client_session(server.mcp) as client:
            tools = (await client.list_tools()).tools
            result = await client.call_tool(
                "search_studies", {"ingredient": "niacinamide", "concern": "acne"}
            )
            return tools, result

    tools, result = anyio.run(run)

    assert [t.name for t in tools] == ["search_studies"]
    assert tools[0].inputSchema["required"] == ["ingredient"]
    assert "when the user asks" in tools[0].description
    assert not result.isError
    assert calls == [("niacinamide", "acne")]
    assert result.structuredContent["result"][0]["pmid"] == "11111111"
