import logging
import os
from typing import List

import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.models.utils import document_exists_by_hash, get_text_hash

logging.basicConfig(level=logging.INFO)


class VectorStoreManager:
    """
    A class to manage a vector store using FAISS and Ollama embeddings.

    This class provides methods to create documents, add them to the vector store,
    perform similarity searches, generate responses using an LLM, and persist/load the store.

    Attributes:
        embeddings (OllamaEmbeddings): An instance of OllamaEmbeddings for embedding text.
        text_splitter (RecursiveCharacterTextSplitter): A text splitter for chunking documents.
        vector_store (FAISS): A FAISS vector store for managing document vectors.
        llm (OllamaLLM): An instance of OllamaLLM for generating responses.
        save_path (str, optional): Path to save/load the vector store.
        index (faiss.Index): The FAISS index (mainly for reference, primary is vector_store.index).
    """

    def __init__(
        self,
        embedding_model: str = "llama3",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        save_path: str = None,  # Path to save/load the vector store
    ):
        """
        Initialize the VectorStoreManager.
        If save_path is provided and exists, it attempts to load the store.
        Otherwise, it initializes a new store.
        """
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True
        )
        self.llm = OllamaLLM(model="gemma3:12b")
        self.save_path = save_path
        self.index = None  # Will be set by _initialize_new_vector_store or load

        if (
            self.save_path
            and os.path.exists(self.save_path)
            and os.path.exists(os.path.join(self.save_path, "index.faiss"))
        ):
            try:
                print(f"Attempting to load vector store from {self.save_path}...")
                self.vector_store = FAISS.load_local(
                    folder_path=self.save_path,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True,  # Important for pickled docstores
                )
                self.index = self.vector_store.index  # Update self.index reference
                print(f"Successfully loaded vector store from {self.save_path}.")
            except Exception as e:
                print(
                    f"Failed to load vector store from {self.save_path}: {e}. Initializing a new one."
                )
                self._initialize_new_vector_store()
        else:
            if self.save_path:
                print(
                    f"No existing vector store found at {self.save_path} or index.faiss is missing. Initializing a new one."
                )
            else:
                print("No save path provided. Initializing a new vector store.")
            self._initialize_new_vector_store()

    def _initialize_new_vector_store(self):
        """Helper method to initialize a new FAISS vector store."""
        print("Initializing a new FAISS vector store...")
        embedding_dim = len(self.embeddings.embed_query("test"))
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.vector_store = FAISS(
            embedding_function=self.embeddings,
            index=self.index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        print(f"New vector store initialized with embedding dimension: {embedding_dim}")

    def save(self, path: str = None):
        """
        Save the vector store to the specified path or the default save_path.
        """
        save_location = path if path else self.save_path
        if not save_location:
            raise ValueError("No path provided or configured to save the vector store.")

        # Ensure the directory exists
        os.makedirs(save_location, exist_ok=True)

        self.vector_store.save_local(save_location)
        print(f"Vector store saved to {save_location}")

    def create_document(self, text: str, metadata: dict = None) -> Document:
        """
        Create a Document object with the given text and metadata.
        """
        if metadata is None:
            metadata = {}
        logging.info("Creating document...")
        return Document(page_content=text, metadata=metadata)

    def add_documents(self, documents: List[Document]):
        """
        Add documents to the vector store after splitting them into chunks.
        """
        chunks = self.text_splitter.split_documents(documents)
        for chunk in chunks:
            text_hash = get_text_hash(chunk.page_content)
            if document_exists_by_hash(self, text_hash):
                logging.info("Documents already in vectore store.")
            else:
                self.vector_store.add_documents(chunks)
                logging.info("Successfully created a new document.")

    def similarity_search(self, query: str, k: int = 1) -> List[Document]:
        """
        Perform a similarity search for the given query and return the top-k documents.
        """
        return self.vector_store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 1):
        """
        Perform a similarity search with scores for the given query and return the top-k results.
        """
        return self.vector_store.similarity_search_with_score(query, k=k)

    def retrieve_context(self, query: str, k: int = 5) -> str:
        """
        Generate a response using the LLM based on the query and retrieved context.
        """
        # Retrieve relevant documents
        retrieved_docs = self.similarity_search(query, k=k)

        # Combine the content of the retrieved documents
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)

        return context

    def generate_response(self, query: str) -> str:
        """
        Generate a response using the LLM based on the query and retrieved context.
        """
        retrieve_context = self.retrieve_context(query)
        # Format the input for the LLM
        prompt = f"Context:\n{retrieve_context}\n\nQuestion:\n{query}\n\nAnswer:"
        # Generate a response using the LLM
        response = self.llm.invoke(prompt)

        return response


if __name__ == "__main__":
    # Ingestion-only dependencies (kagglehub, pandas, ...) are imported here so the
    # app can use VectorStoreManager without installing them.
    from src.models.fetch_documents import ARTICLE_SLUG, DATASET_SLUG, ArticleManager

    # Define a path for saving and loading the vector store
    vector_store_save_path = "./data/my_faiss_vector_store_v3"

    # Initialize the VectorStoreManager, attempting to load if path exists
    vector_store_manager = VectorStoreManager(
        save_path=vector_store_save_path, embedding_model="nomic-embed-text"
    )

    print("Populating the vector store with initial data...")
    article_manager = ArticleManager(DATASET_SLUG, ARTICLE_SLUG)
    navigator_file_name = "wiki_structured_dataset_navigator.jsonl"
    article_manager.load_navigator(navigator_file_name)
    query_topic = "Shawshank Redemption"
    documents_retrieved = article_manager.prepare_documents(
        query_topic, limit=2
    )  # Fetch a few docs

    docs_to_add = []
    if documents_retrieved:
        for doc_data in documents_retrieved:
            new_doc = vector_store_manager.create_document(
                text=doc_data["text"],
                metadata={
                    "name": doc_data["metadata"]["name"],
                    "score": doc_data["metadata"]["score"],
                    "source": doc_data["metadata"].get("source", "N/A"),
                    "hash_key": get_text_hash(doc_data["text"]),
                },
            )
            docs_to_add.append(new_doc)
    else:
        print(f"No documents retrieved for query: {query_topic}")

    # Add some example documents as well, or instead of article manager if it fails
    docs_to_add.extend(
        [
            vector_store_manager.create_document(
                text="The FAISS library allows for efficient similarity search.",
                metadata={"source": "tech-doc"},
            ),
        ]
    )

    if docs_to_add:
        vector_store_manager.add_documents(docs_to_add)
        # Save the store after populating
        vector_store_manager.save()
    else:
        print("No documents were prepared to be added to the vector store.")

    # Now, perform a query
    query = "What does FAISS allow?"
    response = vector_store_manager.generate_response(query)
    print(f"\nQuery: {query}")
    print(f"Response: {response}")

    query2 = "What did the Congress say about Shawshank Redemption?"
    response2 = vector_store_manager.generate_response(query2)
    print(f"\nQuery: {query2}")
    print(f"Response: {response2}")
