# The public MCP server, as a Hugging Face Docker Space. deploy.sh stages this
# file at the Space root, next to src/. Local build: docker build -f deploy/huggingface/Dockerfile .
FROM python:3.11-slim

# ponytail: pins copied from pyproject.toml; uv.lock would install the whole app
# (Streamlit, LangChain, FAISS). Move to a uv dependency group if the server grows.
RUN pip install --no-cache-dir "mcp>=1.20,<2" "httpx>=0.27"

# Spaces run the container as user 1000.
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

COPY --chown=user src/tools ./src/tools
COPY --chown=user src/mcp_server.py ./src/

ENV MCP_TRANSPORT=streamable-http HOST=0.0.0.0 PORT=7860
EXPOSE 7860
CMD ["python", "-m", "src.mcp_server"]
