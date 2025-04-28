import pytest

from src.models.vector_store import VectorStoreManager


@pytest.fixture
def vector_store_manager():
    """
    Fixture to initialize the VectorStoreManager instance for testing.
    """
    return VectorStoreManager()


def test_create_document(vector_store_manager):
    """
    Test the create_document method.
    """
    text = "This is a test document."
    metadata = {"source": "test-source"}
    document = vector_store_manager.create_document(text, metadata)

    assert document.page_content == text
    assert document.metadata == metadata


def test_add_documents(vector_store_manager):
    """
    Test the add_documents method.
    """
    docs = [
        vector_store_manager.create_document("Document 1", {"source": "test1"}),
        vector_store_manager.create_document("Document 2", {"source": "test2"}),
    ]
    vector_store_manager.add_documents(docs)

    # Perform a similarity search to verify documents were added
    results = vector_store_manager.similarity_search("Document", k=2)
    assert len(results) == 2


def test_similarity_search(vector_store_manager):
    """
    Test the similarity_search method.
    """
    docs = [
        vector_store_manager.create_document(
            "Dogs are loyal pets.", {"source": "test1"}
        ),
        vector_store_manager.create_document(
            "Cats are independent pets.", {"source": "test2"}
        ),
    ]
    vector_store_manager.add_documents(docs)

    results = vector_store_manager.similarity_search("loyal pets", k=1)
    assert len(results) == 1
    assert "Dogs are loyal pets." in results[0].page_content


def test_generate_response(vector_store_manager):
    """
    Test the generate_response method.
    """
    docs = [
        vector_store_manager.create_document(
            "Dogs are loyal pets.", {"source": "test1"}
        ),
        vector_store_manager.create_document(
            "Cats are independent pets.", {"source": "test2"}
        ),
    ]
    vector_store_manager.add_documents(docs)

    query = "What are dogs known for?"
    response = vector_store_manager.generate_response(query)

    # Check if the response is a non-empty string
    assert isinstance(response, str)
    assert len(response) > 0
