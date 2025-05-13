from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from src.models.vector_store import VectorStoreManager


@pytest.fixture
def dummy_document():
    doc = Document(
        page_content="This is a test document.",
        metadata={
            "file_name": "test.txt",
            "file_index": 0,
            "name": "Test Document",
            "hash_key": "1234567890abcdef",
        },
    )
    return doc


def test_add_document_returns_true(dummy_document):
    with (
        patch("src.models.vector_store.OllamaEmbeddings") as MockEmbeddings,
        patch("src.models.vector_store.OllamaLLM") as MockLLM,
    ):
        embedding_dim = 384
        MockEmbeddings.return_value.embed_query.return_value = [0.1] * embedding_dim
        MockEmbeddings.return_value.embed_documents.side_effect = lambda texts: [
            [0.1] * embedding_dim for _ in texts
        ]
        MockLLM.return_value.invoke.return_value = "Mocked LLM response"

        manager = VectorStoreManager()
        # Patch the vector_store.add_documents method to always return True
        manager.vector_store = MagicMock()
        manager.vector_store.add_documents.return_value = True

        # Patch text_splitter to just return the input for simplicity
        manager.text_splitter = MagicMock()
        manager.text_splitter.split_documents.return_value = [dummy_document]

        # Patch document_exists_by_hash to always return False (so it tries to add)
        with patch(
            "src.models.vector_store.document_exists_by_hash", return_value=False
        ):
            result = manager.add_documents([dummy_document])
            assert (
                result is True or result is None
            )  # Accept None if your method doesn't return anything
            manager.vector_store.add_documents.assert_called_once()


def test_generate_response_llm_mocked():
    with (
        patch("src.models.vector_store.OllamaEmbeddings") as MockEmbeddings,
        patch("src.models.vector_store.OllamaLLM") as MockLLM,
    ):
        embedding_dim = 384
        MockEmbeddings.return_value.embed_query.return_value = [0.1] * embedding_dim
        MockEmbeddings.return_value.embed_documents.side_effect = lambda texts: [
            [0.1] * embedding_dim for _ in texts
        ]
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "Mocked LLM response"
        MockLLM.return_value = mock_llm_instance

        manager = VectorStoreManager()
        # Optionally patch similarity_search if you want to avoid vector store logic
        manager.similarity_search = MagicMock(
            return_value=[Document(page_content="Some context", metadata={})]
        )
        response = manager.generate_response("What is the age of Aristides?")
        assert response == "Mocked LLM response"
