from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.models.responses import clean_llm_response

APP_PATH = "../../streamlit_app.py"


def test_no_assistant_reply_before_user_message():
    with patch("src.views.chat.response_generator_rag") as mock_rag:
        at = AppTest.from_file(APP_PATH).run()

    mock_rag.assert_not_called()
    assert at.session_state.messages == []


def test_one_reply_per_user_message():
    with patch(
        "src.views.chat.response_generator_rag", return_value="Hello!"
    ) as mock_rag:
        at = AppTest.from_file(APP_PATH).run()
        at.chat_input[0].set_value("Hi").run()
        # A rerun with no new input must not make the assistant answer itself
        at.run()

    assert mock_rag.call_count == 1
    assert at.session_state.messages == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
    ]


def test_clean_llm_response_keeps_leading_letters():
    assert clean_llm_response("AI: I think so.") == "I think so."
    assert clean_llm_response("I think so.") == "I think so."
    assert clean_llm_response("AI agents help.") == "AI agents help."
