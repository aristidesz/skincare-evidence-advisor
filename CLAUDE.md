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
```

After changing dependencies, regenerate the lockfile with `uvx --from uv==0.6.14 uv lock`. The lock is in format revision 1, and newer uv rewrites the whole file.

## Code map

- `streamlit_app.py`: entry point. Loads settings, renders the chat.
- `src/config.py`: `LLMSettings` from env vars (`LLM_PROVIDER` = `ollama` | `openrouter`, plus `<PROVIDER>_MODEL/_BASE_URL/_API_KEY`). See `.env.example`.
- `src/models/llm.py`: one OpenAI-compatible client for Ollama and OpenRouter, `stream_chat`.
- `src/models/responses.py`: system prompt + `build_messages` + `response_generator_llm`.
- `src/views/chat.py`: the chat UI (history in `st.session_state`, one reply per user message).
- `src/tools/studies.py`: `search_studies` on Europe PMC plus its tool schema `SEARCH_STUDIES_TOOL`. Not yet called by the model.
- `src/models/rag.py`, `vector_store.py`, `fetch_documents.py`: legacy Wikipedia RAG. Unused, and due to be replaced by the clinical-study index.
- `docs/data-sources.md`: where science and product data come from, and why.

## How we work

- **Teach before build.** Before each step, give a short lesson (what, why, how) tied to agent concepts, then ask one check question and wait for the answer. Then build.
- **One concept per PR**, small enough to read in minutes. Agree on the scope before writing it.
- Branch from `dev` and open PRs into `dev`. `main` is for releases only. Never push to `dev` or `main` directly. The owner reviews and merges.
- PR descriptions open with **Before:** and **After:** paragraphs, then show before/after code for each change and how to check it.
- No Claude session or project links in PR descriptions or commit messages.
- Tests mock the network (`httpx.MockTransport`, mocked OpenAI client, Streamlit `AppTest`).

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
- [ ] **Tool-calling loop:** the model decides to call `search_studies`. Show the tool calls, and set step and context budgets.
- [ ] Skincare system prompt and context budget (sliding window, trimmed tool results)
- [ ] INCI ingredient-list parser (above 1% in descending order, the rest in any order)
- [ ] Graded evidence index for about 15 core actives, with citations
- [ ] Open Beauty Facts product lookup
- [ ] Guardrails, product cards with affiliate disclosure
- [ ] Evals in CI, Langfuse tracing, deploy (Streamlit Community Cloud), MCP server

Known gaps in `search_studies`:
- no synonyms yet (niacinamide vs nicotinamide);
- results lean recent.
