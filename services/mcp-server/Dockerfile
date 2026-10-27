# The MCP server image (src/mcp_server.py), as run by the Hugging Face Space.
# Build context is the repo root. Use: scripts/docker.sh mcp-server build
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /bin/uv

# Hugging Face runs containers as user 1000.
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Dependencies before code: this layer stays cached until pyproject.toml or uv.lock change.
COPY --chown=user pyproject.toml uv.lock ./
RUN uv sync --frozen --only-group server

COPY --chown=user src/tools ./src/tools
COPY --chown=user src/mcp_server.py ./src/

EXPOSE 7860
CMD [".venv/bin/python", "-m", "src.mcp_server"]
