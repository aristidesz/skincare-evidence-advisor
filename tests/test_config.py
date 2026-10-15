import pytest

from src.config import load_llm_settings


def test_defaults_to_local_ollama(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    settings = load_llm_settings()
    assert settings.provider == "ollama"
    assert settings.base_url == "http://localhost:11434/v1"
    assert settings.api_key  # the OpenAI client needs a non-empty key


def test_openrouter_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        load_llm_settings("openrouter")


def test_openrouter_reads_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model:free")
    settings = load_llm_settings()
    assert settings.base_url == "https://openrouter.ai/api/v1"
    assert settings.model == "some/model:free"
    assert settings.api_key == "sk-test"


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        load_llm_settings("not-a-provider")
