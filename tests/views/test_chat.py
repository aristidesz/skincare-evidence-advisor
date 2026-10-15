from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP_PATH = "../../streamlit_app.py"


def test_no_assistant_reply_before_user_message():
    with patch("src.views.chat.response_generator_llm") as mock_llm:
        at = AppTest.from_file(APP_PATH).run()

    mock_llm.assert_not_called()
    assert at.session_state.messages == []


def test_one_reply_per_user_message():
    with patch(
        "src.views.chat.response_generator_llm", return_value=iter(["Hel", "lo!"])
    ) as mock_llm:
        at = AppTest.from_file(APP_PATH).run()
        at.chat_input[0].set_value("Hi").run()
        # A rerun with no new input must not make the assistant answer itself
        at.run()

    assert mock_llm.call_count == 1
    assert at.session_state.messages == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]


def test_model_error_is_shown_not_raised():
    with patch(
        "src.views.chat.response_generator_llm",
        side_effect=ConnectionError("connection refused"),
    ):
        at = AppTest.from_file(APP_PATH).run()
        at.chat_input[0].set_value("Hi").run()

    assert not at.exception
    assert "connection refused" in at.error[0].value


def test_missing_openrouter_key_stops_the_app(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file(APP_PATH).run()

    assert "OPENROUTER_API_KEY" in at.error[0].value
    assert len(at.chat_input) == 0
