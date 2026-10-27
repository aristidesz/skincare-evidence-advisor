# Skincare Evidence Advisor

A Streamlit chat app that answers skincare questions with what clinical studies say about an ingredient, and how strong that evidence is. No marketing claims, and not medical advice. It is also a portfolio project: every piece should be explainable in an interview.

## Commands

```sh
uv sync --all-extras                          # install (creates .venv)
OLLAMA_CONTEXT_LENGTH=16384 ollama serve      # local model server; default model gemma4:12b
uv run streamlit run streamlit_app.py         # run the app
uv run pytest -m "not e2e"                    # tests (CI runs the same)
uv run black --check . && uv run flake8 tests # lint (CI runs the same)
uv run python -m src.tools.studies niacinamide acne   # try the study search live
scripts/docker.sh mcp-server build|run                # build or run a service image
scripts/docker.sh clean                               # remove leftover images and old build cache
```

After changing dependencies, regenerate the lockfile with `uvx --from uv==0.6.14 uv lock`. The lock is in format revision 1, and newer uv rewrites the whole file.

## Code map

- `streamlit_app.py`: entry point. Loads settings, renders the chat.
- `src/config.py`: `LLMSettings` from env vars (`LLM_PROVIDER` = `ollama` | `openrouter`, plus `<PROVIDER>_MODEL/_BASE_URL/_API_KEY`). See `.env.example`.
- `src/models/llm.py`: one OpenAI-compatible client for Ollama and OpenRouter, `stream_chat`.
- `src/models/responses.py`: system prompt + `build_messages` + `response_generator_llm`.
- `src/views/chat.py`: the chat UI (history in `st.session_state`, one reply per user message).
- `src/tools/studies.py`: `search_studies` on Europe PMC plus its tool schema `SEARCH_STUDIES_TOOL`. Not yet called by the model.
- `src/mcp_server.py`: the same tool as an MCP server (`mcp` 2.x, Streamable HTTP on port 7860, stateless, stateless). Inputs are length-limited and results are cached in memory per calendar quarter; failures are never cached.
- `services/<name>/Dockerfile`: one folder per deployable service (today only `mcp-server`). Build context is the repo root; `scripts/docker.sh` builds and runs them.
- `src/models/rag.py`, `vector_store.py`, `fetch_documents.py`: legacy Wikipedia RAG. Unused, and due to be replaced by the clinical-study index.
- `render.yaml`: Render Blueprint for the public MCP server (free Docker web service, tracks `dev`).
- `docs/data-sources.md`: where science and product data come from, and why.
- `docs/mcp-server.md`: build, run and curl the MCP server; Docker cleanup.

## Design decisions

- **Own harness, no agent framework yet.** The loop is built by hand on the `openai` client, so every line can be explained. Open-source libraries are used around it (Streamlit, MCP SDK, Langfuse later). Porting to a framework such as LangGraph comes later, as a comparison.
- **Tools** are plain tested functions plus a schema whose description says *when* to use them. The harness executes tools, not the model.
- **Guardrails live in code, not only in the prompt.** Examples are red-flag symptoms leading to "see a GP or dermatologist", and legal concentration caps.
- **Ingredient percentages are usually not public.** Show "listed / estimated / stated by brand", never an invented number.
- **No scraping.** INCIDecoder, Skinsort and CosDNA have no API. Use Europe PMC, PubMed, CosIng, Open Beauty Facts and user-pasted ingredient lists. Amazon is only for the buy link, with an affiliate disclosure.

## Roadmap

Done:
- [x] Model layer (Ollama/OpenRouter)
- [x] Chat bug fixes
- [x] `search_studies` tool

Next:
- [ ] **Tool-calling loop:** the model decides to call `search_studies`. Show the tool calls, and set step and context budgets. When `search_studies` raises `StudySearchError`, show a warning in the chat and tell the model it cannot answer from memory as if it were evidence.
- [ ] Skincare system prompt and context budget (sliding window, trimmed tool results)
- [ ] INCI ingredient-list parser (above 1% in descending order, the rest in any order)
- [ ] Graded evidence index for about 15 core actives, with citations
- [ ] Open Beauty Facts product lookup
- [ ] Guardrails, product cards with affiliate disclosure
- [ ] Evals in CI, Langfuse tracing, deploy (Streamlit Community Cloud), MCP server

Known gaps in `search_studies`:
- no synonyms yet (niacinamide vs nicotinamide);
- results lean recent.
