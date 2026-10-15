from streamlit.testing.v1 import AppTest


def test_app_renders_without_calling_the_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    at = AppTest.from_file("../streamlit_app.py").run()
    assert not at.exception
    assert at.title[0].value == "Skincare Advisor"
    # No assistant message until the user asks something.
    assert len(at.chat_message) == 0


def test_missing_openrouter_key_shows_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file("../streamlit_app.py").run()
    assert "OPENROUTER_API_KEY" in at.error[0].value
