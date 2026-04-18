import hashlib
import logging
from typing import List

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from src.config import (
    CHROMA_DIR,
    CHROMA_COLLECTION,
    EMBED_MODEL,
    OLLAMA_BASE_URL,
)

logger = logging.getLogger(__name__)

class ChromaWrapper:
    """Wrapper for ChromaDB vector store using LangChain abstractions."""

    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model=EMBED_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
        self.vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION,
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DIR),
        )

    def _generate_id(self, doc: Document) -> str:
        """Generate a deterministic ID based on content and source metadata."""
        content = doc.page_content
        source = doc.metadata.get("source", "unknown")
        # Use SHA-256 for collision resistance and idempotency
        return hashlib.sha256(f"{content}{source}".encode()).hexdigest()

    def add_documents(self, docs: List[Document]) -> None:
        """Add documents to ChromaDB with deduplication."""
        if not docs:
            return

        # Deduplicate within the batch using IDs
        doc_map = {self._generate_id(doc): doc for doc in docs}
        
        ids = list(doc_map.keys())
        clean_docs = list(doc_map.values())
        
        self.vectorstore.add_documents(documents=clean_docs, ids=ids)
        logger.info(f"Successfully processed {len(clean_docs)} unique documents into collection '{CHROMA_COLLECTION}'.")

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Perform semantic search for documents similar to the query."""
        return self.vectorstore.similarity_search(query, k=k)

    def collection_stats(self) -> dict:
        """Return statistics about the collection."""
        count = self.vectorstore._collection.count()
        return {
            "total_chunks": count,
            "collection_name": CHROMA_COLLECTION,
        }
