import hashlib


def is_similar_document_present(vector_store_manager, text, threshold=0.95):
    results = vector_store_manager.similarity_search(text, k=1)
    if results:
        # Compute similarity (cosine or other, depending on your embeddings)
        # If above threshold, consider as duplicate
        return True
    return False


def get_text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def document_exists_by_hash(vector_store_manager, text_hash: str) -> bool:
    for doc in vector_store_manager.vector_store.docstore._dict.values():
        if get_text_hash(doc.page_content) == text_hash:
            return True
    return False


def document_exists(vector_store_manager, unique_id: str) -> bool:
    # Search by unique metadata field (e.g., name or file_name)
    for doc in vector_store_manager.vector_store.docstore._dict.values():
        if doc.metadata.get("hash_key") == unique_id:
            return True
    return False
