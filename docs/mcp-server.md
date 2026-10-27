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

## Deploy to Render

[render.yaml](../render.yaml) is a Render Blueprint: a free Docker web service built from the same
`services/mcp-server/Dockerfile`, on Render's machines, from the `dev` branch. Every merge to `dev`
redeploys it. The server listens on 7860 and the Blueprint sets `PORT=7860`, so Render forwards there.

The public instance is `https://skincare-evidence-mcp.onrender.com/mcp`.

One-time setup (to deploy your own copy):

1. Create an account at render.com (signing in with GitHub is easiest) and let it read this repo.
2. Dashboard, then New, then **Blueprint**: pick the repo and the `dev` branch, then Apply.
   If Render asks for a card, it is normally a small verification hold; the plan is `free`, so
   there should be no charge.
3. Watch the deploy log until the service is **Live**. Its URL is on the service page:
   `https://<service>.onrender.com`.

Then use the URL instead of localhost (for your own copy, the one on its service page):

```sh
MCP_URL=https://skincare-evidence-mcp.onrender.com/mcp
curl -s -X POST $MCP_URL \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

claude mcp add --transport http skincare-evidence $MCP_URL   # then ask Claude about an ingredient
```

Free-tier behaviour ([Render docs](https://render.com/docs/free)): the service sleeps after 15 minutes
without requests and takes about a minute to wake, so the first request after a pause can be slow or
time out; retry it. There are 750 instance hours a month, and the filesystem is wiped on every restart.
Search results are cached in memory per calendar quarter (an empty cache after a sleep or redeploy is
normal), and a failed search is never cached. New (uncached) searches are capped at 30 a minute across all callers, so a busy minute can answer
"Too many searches right now" while questions asked before still work. The endpoint has no authentication.

## When it does not work

| What you see | Cause |
|---|---|
| `Connection refused` | The container is not running, or the port is mapped differently. |
| `port is already allocated` on run | An earlier container still holds 7860. Stop it with `docker ps`, then `docker stop <id>`. |
| `curl` never returns | A GET (no `-X POST`) opens an event stream that never closes. Ctrl+C. |
| Render deploy fails because it finds no open port | `PORT` in `render.yaml` does not match the port in `src/mcp_server.py` (7860). |
| `Too many searches right now` | The cap of 30 new Europe PMC searches a minute was reached. Wait a minute; repeated questions are still answered from the cache. |
| `isError: true` | The tool ran and failed, for example Europe PMC was unreachable. Read the `content` text. |
