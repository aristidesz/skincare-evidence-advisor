from unittest.mock import patch

import pandas as pd
import pytest

from src.models.fetch_documents import ArticleManager


@pytest.fixture
def article_manager():
    """
    Fixture to initialize the ArticleManager instance for testing.
    """
    dataset_slug = "mehranism/wikimedia-structured-dataset-navigator-jsonl"
    article_slug = "wikimedia-foundation/wikipedia-structured-contents"
    return ArticleManager(dataset_slug, article_slug)


@pytest.fixture
def mock_navigator_df():
    """
    Fixture to provide a mock navigator DataFrame.
    """
    data = {
        "file_name": ["enwiki_namespace_0_0.jsonl", "enwiki_namespace_0_1.jsonl"],
        "file_index": [0, 1],
        "name": ["Shawshank Redemption", "The Godfather"],
    }
    return pd.DataFrame(data)


@patch("kagglehub.dataset_download")
def test_load_navigator(mock_dataset_download, article_manager, tmp_path):
    """
    Test the load_navigator method.
    """
    # Mock the kagglehub.dataset_download method
    mock_file_path = tmp_path / "navigator.jsonl"
    mock_file_path.write_text('{"file_name": "test.jsonl", "file_index": 0}\n')
    mock_dataset_download.return_value = str(mock_file_path)

    # Call the method
    article_manager.load_navigator("navigator.jsonl")

    # Assertions
    assert article_manager.navigator_df is not None
    assert not article_manager.navigator_df.empty
    mock_dataset_download.assert_called_once_with(
        article_manager.dataset_slug, path="navigator.jsonl"
    )


def test_fuzzy_search(article_manager, mock_navigator_df):
    """
    Test the fuzzy_search method.
    """
    # Set the mock navigator DataFrame
    article_manager.navigator_df = mock_navigator_df

    # Perform a fuzzy search
    results = article_manager.fuzzy_search("Shawshank", column_name="name", limit=1)

    # Assertions
    assert len(results) == 1
    assert results[0]["name"] == "Shawshank Redemption"
    assert results[0]["score"] > 0


@patch("kagglehub.dataset_download")
def test_fetch_article(mock_dataset_download, article_manager, tmp_path):
    """
    Test the fetch_article method.
    """
    # Mock the kagglehub.dataset_download method
    mock_file_path = tmp_path / "article.jsonl"
    mock_file_path.write_text(
        '{"description": "A great movie.", "abstract": "A prison story.", "sections": [{"text": "Details about the movie."}]}\n'
    )
    mock_dataset_download.return_value = str(mock_file_path)

    # Call the method
    text = article_manager.fetch_article("enwiki_namespace_0_0.jsonl", file_index=0)

    # Assertions
    assert "A great movie." in text
    assert "A prison story." in text
    assert "Details about the movie." in text
    mock_dataset_download.assert_called_once_with(
        article_manager.article_slug,
        path="enwiki_namespace_0/enwiki_namespace_0_0.jsonl",
    )


@patch("src.models.fetch_documents.ArticleManager.fetch_article")
def test_prepare_documents(mock_fetch_article, article_manager, mock_navigator_df):
    """
    Test the prepare_documents method.
    """
    # Set the mock navigator DataFrame
    article_manager.navigator_df = mock_navigator_df

    # Mock the fetch_article method
    mock_fetch_article.return_value = "Mock article content."

    # Call the method
    documents = article_manager.prepare_documents("Shawshank", limit=1)

    # Assertions
    assert len(documents) == 1
    assert documents[0]["text"] == "Mock article content."
    assert documents[0]["metadata"]["name"] == "Shawshank Redemption"
    mock_fetch_article.assert_called_once_with("enwiki_namespace_0_0.jsonl", 0)
