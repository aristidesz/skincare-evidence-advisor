"""LLM provider settings.

Values come from environment variables. On Streamlit Community Cloud, top-level
secrets are exposed as environment variables too, so the same code works locally
and when deployed.
"""

import os
from dataclasses import dataclass
from typing import Optional

# Both providers speak the OpenAI-compatible Chat Completions API, so switching
# between them only changes the base URL, the API key and the model name.
PROVIDER_DEFAULTS = {
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "gemma3:12b",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
    },
}


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    base_url: str
    model: str
    api_key: str


def load_llm_settings(provider: Optional[str] = None) -> LLMSettings:
    """Build settings for the chosen provider (defaults to LLM_PROVIDER, then ollama).

    Each value can be overridden with <PROVIDER>_BASE_URL, <PROVIDER>_MODEL and
    <PROVIDER>_API_KEY, e.g. OPENROUTER_MODEL.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()
    if provider not in PROVIDER_DEFAULTS:
        raise ValueError(
            f"Unknown LLM provider '{provider}'. "
            f"Choose one of: {', '.join(PROVIDER_DEFAULTS)}."
        )

    defaults = PROVIDER_DEFAULTS[provider]
    prefix = provider.upper()
    # Ollama ignores the key, but the OpenAI client requires a non-empty one.
    default_key = "ollama" if provider == "ollama" else ""
    api_key = os.getenv(f"{prefix}_API_KEY", default_key)
    if not api_key:
        raise ValueError(f"{prefix}_API_KEY is not set.")

    return LLMSettings(
        provider=provider,
        base_url=os.getenv(f"{prefix}_BASE_URL", defaults["base_url"]),
        model=os.getenv(f"{prefix}_MODEL", defaults["model"]),
        api_key=api_key,
    )
