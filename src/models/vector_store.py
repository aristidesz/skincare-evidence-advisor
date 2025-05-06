from typing import List

import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter


class VectorStoreManager:
    """
    A class to manage a vector store using FAISS and Ollama embeddings.

    This class provides methods to create documents, add them to the vector store,
    perform similarity searches, and generate responses using an LLM.

    Attributes:
        embeddings (OllamaEmbeddings): An instance of OllamaEmbeddings for embedding text.
        text_splitter (RecursiveCharacterTextSplitter): A text splitter for chunking documents.
        index (faiss.Index): A FAISS index for storing and searching vectors.
        vector_store (FAISS): A FAISS vector store for managing document vectors.
        llm (OllamaLLM): An instance of OllamaLLM for generating responses.

    Example usage:
        vector_store_manager = VectorStoreManager()
        docs = [
            vector_store_manager.create_document("Dogs are great companions.", {"source": "mammal-pets-doc"}),
            vector_store_manager.create_document("Cats are independent pets.", {"source": "mammal-pets-doc"}),
        ]
        vector_store_manager.add_documents(docs)
        response = vector_store_manager.generate_response("What do dogs represent?")
        print(response)

    """

    def __init__(
        self,
        embedding_model: str = "llama3",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize the VectorStoreManager with an embedding model and text splitting parameters.
        """
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True
        )
        # Initialise FAISS dimension using a dynamic query
        self.embedding_dim = len(self.embeddings.embed_query("test"))
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.vector_store = FAISS(
            embedding_function=self.embeddings,
            index=self.index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        self.llm = OllamaLLM(model="gemma3:12b")

    def create_document(self, text: str, metadata: dict = None) -> Document:
        """
        Create a Document object with the given text and metadata.
        """
        if metadata is None:
            metadata = {}
        return Document(page_content=text, metadata=metadata)

    def add_documents(self, documents: List[Document]):
        """
        Add documents to the vector store after splitting them into chunks.
        """
        chunks = self.text_splitter.split_documents(documents)
        self.vector_store.add_documents(chunks)

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

    def generate_response(self, query: str) -> str:
        """
        Generate a response using the LLM based on the query and retrieved context.
        """
        # Retrieve relevant documents
        retrieved_docs = self.similarity_search(query, k=5)

        # Combine the content of the retrieved documents
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)

        # Format the input for the LLM
        prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"

        # Generate a response using the LLM
        response = self.llm.invoke(prompt)

        return response


if __name__ == "__main__":
    # Initialize the VectorStoreManager
    vector_store_manager = VectorStoreManager()

    # Example documents
    docs = [
        vector_store_manager.create_document(
            text="My name is Aristides and I am 34 years old.",
            metadata={"source": "mammal-pets-doc"},
        ),
        vector_store_manager.create_document(
            text="His postcode is E15.",
            metadata={"source": "mammal-pets-doc"},
        ),
    ]

    # Add documents to the vector store
    vector_store_manager.add_documents(docs)

    query = "What is the age of Aristides and what is his postcode address?"
    response = vector_store_manager.generate_response(query)
    print(response)
