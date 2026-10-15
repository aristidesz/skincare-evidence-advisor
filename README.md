# Skincare Advisor

An evidence-based skincare assistant: ask what actually works for your skin and get
answers grounded in clinical studies, not marketing.

> Status: early build. The chat runs on a local or hosted LLM; clinical-study
> retrieval, tools and the agent loop are coming next (see Roadmap).

## How it works (so far)

- **Model layer** (`src/models/llm.py`): one OpenAI-compatible client that talks to
  either **Ollama** (local, free, private) or **OpenRouter** (hosted, free models
  available). Switching is configuration only: base URL, API key and model.
- **Chat harness** (`src/views/chat.py`, `src/models/responses.py`): the LLM is
  stateless, so the app keeps the conversation in Streamlit session state and sends
  the system prompt plus the full history on every turn, streaming the reply back.

## Run locally

1. Install [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com/), then
   pull a model: `ollama pull gemma3:12b`
2. Install dependencies: `uv sync`
3. Start the app: `uv run streamlit run streamlit_app.py`

To use OpenRouter instead, copy `.env.example`, set `LLM_PROVIDER=openrouter` and
`OPENROUTER_API_KEY`, and export them before starting the app.

## Development

```sh
uv sync --all-extras          # app + ingestion + test + lint dependencies
uv run pytest -m "not e2e"    # unit tests
uv run black . && uv run flake8 src streamlit_app.py
```

## Roadmap

1. Model layer: Ollama / OpenRouter with streaming ✅
2. Chat harness and UI: conversation state, context limits, professional UI
3. Knowledge: ingest clinical studies (PubMed / Europe PMC) into a vector store
4. Tools: evidence lookup, contraindication checks, product search
5. Agent loop: ReAct with step and cost budgets
6. Guardrails: medical safety, mandatory citations, affiliate disclosure
7. Evals and tracing: golden set in CI, Langfuse
8. MCP server exposing the evidence base

## Disclaimer

This app provides general educational information, not medical advice.

Built by [aristidesz](https://github.com/aristidesz).
