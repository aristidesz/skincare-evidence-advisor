import json
import os
from typing import List

import kagglehub
import pandas as pd
from rapidfuzz import fuzz, process
from tqdm import tqdm

DATASET_SLUG = "mehranism/wikimedia-structured-dataset-navigator-jsonl"
ARTICLE_SLUG = "wikimedia-foundation/wikipedia-structured-contents"


class ArticleManager:
    """
    A class to manage searching, downloading, and processing articles from a Kaggle dataset.

    This class allows you to search for articles using a keyword, download the relevant articles,
    and create text documents that can be passed to a vector store.

    Attributes:
        dataset_slug (str): The Kaggle dataset slug.
        navigator_df (pd.DataFrame): A DataFrame containing the article metadata.
    """

    def __init__(self, dataset_slug: str, article_slug: str):
        """
        Initialize the ArticleManager with the Kaggle dataset slug.

        Args:
            dataset_slug (str): The Kaggle dataset slug.
            article_slug (str): The article slug to be used for fetching articles.
        """
        self.dataset_slug = dataset_slug
        self.article_slug = article_slug
        self.navigator_df = None
        self.download_dir = "./data/"

    def load_navigator(self, file_name: str):
        """
        Load the navigator file (JSONL) into a DataFrame.

        Args:
            file_name (str): The name of the navigator file in the dataset.
        """
        file_path = kagglehub.dataset_download(self.dataset_slug, path=file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Failed to download {file_name} from {self.dataset_slug}"
            )
        self.navigator_df = self._load_jsonl(file_path)

    @staticmethod
    def _load_jsonl(file_path: str, max_records: int = None) -> pd.DataFrame:
        """
        Load a JSONL file into a DataFrame.

        Args:
            file_path (str): Path to the JSONL file.
            max_records (int, optional): Maximum number of records to load.

        Returns:
            pd.DataFrame: A DataFrame containing the JSONL data.
        """
        records = []
        with open(file_path, "r", encoding="utf-8") as file:
            for i, line in enumerate(tqdm(file, desc="Loading JSONL")):
                if max_records and i >= max_records:
                    break
                records.append(json.loads(line))
        return pd.DataFrame(records)

    def fuzzy_search(
        self, query: str, column_name: str = "name", limit: int = 5
    ) -> List[dict]:
        """
        Perform a fuzzy search to find articles matching a query.

        Args:
            query (str): User's search query.
            column_name (str): Column to search (e.g., 'name').
            limit (int): Number of top matches to return.

        Returns:
            List[dict]: List of dictionaries with index, name, and score for matches.
        """
        if self.navigator_df is None:
            raise ValueError(
                "Navigator DataFrame is not loaded. Call `load_navigator` first."
            )

        article_names = self.navigator_df[column_name].tolist()
        matches = process.extract(
            query, article_names, scorer=fuzz.token_sort_ratio, limit=limit
        )

        results = []
        for match in matches:
            name, score = match[0], match[1]
            index = self.navigator_df[self.navigator_df[column_name] == name].index[0]
            results.append({"index": index, "name": name, "score": score})
        return results

    def fetch_article(self, file_name: str, file_index: int) -> str:
        """
        Fetch and process an article's content.

        Args:
            file_name (str): Name of the file containing the article.
            file_index (int): Index of the article in the file.

        Returns:
            str: The processed text content of the article.
        """
        # Ensure the file_name is correct and does not duplicate the directory structure
        if not file_name.startswith("enwiki_namespace_0/"):
            file_name = f"enwiki_namespace_0/{file_name}"

        # Download the article file using kagglehub
        try:
            file_path = kagglehub.dataset_download(self.article_slug, path=file_name)
        except Exception as e:
            raise FileNotFoundError(
                f"Failed to download {file_name} from {self.article_slug}. Error: {e}"
            )

        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_name} was not found at {file_path}.")

        # Load the JSONL file into a DataFrame
        article_df = self._load_jsonl(file_path)

        # Clean up the downloaded file
        # os.remove(file_path)

        # Extract the specific article
        article_row = article_df.iloc[file_index]
        return self._build_text(article_row)

    @staticmethod
    def _build_text(row: pd.Series) -> str:
        """
        Build a text representation of an article from its row data.

        Args:
            row (pd.Series): A row of article data.

        Returns:
            str: The combined text content of the article.
        """
        text = ""
        if isinstance(row.get("description"), str):
            text += row["description"] + "\n"
        if isinstance(row.get("abstract"), str):
            text += row["abstract"] + "\n"
        if isinstance(row.get("sections"), list):
            for section in row["sections"]:
                if "text" in section:
                    text += section["text"] + "\n"
        return text.strip()

    def prepare_documents(self, query: str, limit: int = 5) -> List[dict]:
        """
        Search for articles, download them, and create text documents.

        Args:
            query (str): The search query.
            limit (int): Number of top matches to process.

        Returns:
            List[dict]: A list of documents with text and metadata.
        """
        search_results = self.fuzzy_search(query, limit=limit)
        documents = []
        for result in search_results:
            index = result["index"]
            file_name = self.navigator_df.iloc[index]["file_name"]
            file_index = self.navigator_df.iloc[index]["file_index"]
            text = self.fetch_article(file_name, file_index)
            documents.append(
                {
                    "text": text,
                    "metadata": {"name": result["name"], "score": result["score"]},
                }
            )
        return documents


if __name__ == "__main__":
    # Initialize the ArticleManager
    article_manager = ArticleManager(DATASET_SLUG, ARTICLE_SLUG)

    # Load the navigator file
    navigator_file_name = "wiki_structured_dataset_navigator.jsonl"
    article_manager.load_navigator(navigator_file_name)

    # Search for articles and create documents
    query = "Shawshank Redemption"
    documents = article_manager.prepare_documents(query, limit=3)

    # Print the documents
    for doc in documents:
        print(f"Metadata: {doc['metadata']}")
        print(f"Text: {doc['text'][:500]}...")
