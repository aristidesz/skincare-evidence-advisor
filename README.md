# Skincare Evidence Advisor

Built with ❤️ by [aristidesz](https://github.com/aristidesz)

A chat app that answers skincare questions with what the clinical studies say about an ingredient, and how strong that evidence is. No marketing claims.

> General educational information only, not medical advice. For a changing mole, an infection or severe acne, see a GP or dermatologist.

## Status

Early build. Right now it's a working chat with a local or hosted open-source model.

- [x] Chat app with one model client for Ollama (local) and OpenRouter (hosted)
- [ ] Chat harness: skincare system prompt, UI shell, context budget
- [ ] Knowledge base: clinical studies from PubMed / Europe PMC
- [ ] Evidence grading and citations in answers
- [ ] Agent loop with tools and a skin profile
- [ ] Guardrails and product suggestions (with affiliate disclosure)
- [ ] Evals, tracing and a public deployment

## Quickstart

You need [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com).

```sh
git clone https://github.com/aristidesz/skincare-evidence-advisor.git
cd skincare-evidence-advisor

ollama pull gemma4:12b
OLLAMA_CONTEXT_LENGTH=16384 ollama serve   # keep this running

uv sync --all-extras
uv run streamlit run streamlit_app.py
```

The app uses `gemma4:12b` on Ollama by default. To use OpenRouter or another model, copy `.env.example` to `.env`, set `LLM_PROVIDER`, `OPENROUTER_API_KEY` or `OLLAMA_MODEL`, and run `uv run --env-file .env streamlit run streamlit_app.py`.

## Tests

```sh
uv run pytest -m "not e2e"
uv run black --check .
```

Feature branches merge into `dev`. `main` holds releases.
