# MCP server

`search_studies` (clinical studies on Europe PMC) served as an [MCP](https://modelcontextprotocol.io)
tool over Streamable HTTP. Code: [src/mcp_server.py](../src/mcp_server.py). Image recipe:
[services/mcp-server/Dockerfile](../services/mcp-server/Dockerfile).

## Build, run, clean up

Needs Docker Desktop running (`open -a Docker`). Run from anywhere in the repo.

```sh
scripts/docker.sh mcp-server build   # image skincare-mcp-server; then drops the previous untagged build
scripts/docker.sh mcp-server run     # serves http://localhost:7860/mcp, Ctrl+C to stop (container is removed)
scripts/docker.sh clean              # untagged images + build cache older than 7 days, then shows disk use
```

A service is any `services/<name>/Dockerfile`. A new MCP server means a new folder there; the script
does not change. The build context is the repo root, and `services/<name>/Dockerfile.dockerignore` is
an allowlist of what is sent to Docker (the context should be about 1.4 MB, almost all `uv.lock`).
Rebuilds after a code change take seconds: the `uv sync` layer stays `CACHED` until `pyproject.toml`
or `uv.lock` change.

Disk check: `docker system df`. `scripts/docker.sh clean` keeps recent build cache on purpose, because
that cache is what makes rebuilds fast.

## Talk to it with curl

MCP is JSON-RPC over HTTP POST. With the container running, in a second terminal:

```sh
# 1. Discovery: what tools exist, and their input and output schemas?
curl -s -X POST localhost:7860/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# 2. Use: call search_studies
curl -s -X POST localhost:7860/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_studies","arguments":{"ingredient":"niacinamide","concern":"acne"}}}'
```

- `Accept` lists both JSON and `text/event-stream`: the MCP spec requires clients to send it, because
  the server may answer either way. This server (`mcp` 2.3) is lenient and answers without it, but
  other servers can reject the request, so keep it.
- The server is stateless, so there is no `initialize` step: every request stands alone.
- `id` ties a reply to its request.
- The reply is a server-sent event: `event: message`, then `data: {"jsonrpc":"2.0",...}`.
  The `result` of a `tools/call` has `content` (one JSON text per study) and `structuredContent`
  (the same studies as typed JSON, matching the tool's `outputSchema`).

To read the reply as JSON, add this to either command:

```sh
... | sed -n 's/^data: //p' | python3 -m json.tool
```

## When it does not work

| What you see | Cause |
|---|---|
| `Connection refused` | The container is not running, or the port is mapped differently. |
| `port is already allocated` on run | An earlier container still holds 7860. Stop it with `docker ps`, then `docker stop <id>`. |
| `curl` never returns | A GET (no `-X POST`) opens an event stream that never closes. Ctrl+C. |
| `isError: true` | The tool ran and failed, for example Europe PMC was unreachable. Read the `content` text. |
