"""ChromaDB vector store for embeddings"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import uuid


class ChromaStore:
    """ChromaDB vector store for document embeddings"""

    def __init__(self, persist_directory: str, collection_name: str = "documents"):
        """
        Initialize ChromaDB store

        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize ChromaDB client with persistence
        import os
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=chromadb.Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Add documents to the vector store

        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = []

        for chunk in chunks:
            metadata = {k: str(v) for k, v in chunk.items() if k != 'text'}
            metadatas.append(metadata)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        print(f"Added {len(chunks)} documents to vector store")

    def search(self, query_embedding: List[float], top_k: int = 5) -> Dict:
        """
        Search for similar documents

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            Dictionary with search results
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else []
        }

    def delete_by_source(self, source_file: str) -> int:
        """
        Delete all documents from a specific source file

        Args:
            source_file: Name of the source file

        Returns:
            Number of documents deleted
        """
        # Get all documents with this source
        results = self.collection.get(
            where={"source": source_file}
        )

        if not results['ids']:
            return 0

        # Delete the documents
        self.collection.delete(ids=results['ids'])
        deleted_count = len(results['ids'])
        print(f"  🗑️  Deleted {deleted_count} old chunks from {source_file}")
        return deleted_count

    def delete_collection(self):
        """Delete the collection"""
        self.client.delete_collection(name=self.collection_name)
        print(f"Deleted collection: {self.collection_name}")

    def get_collection_info(self) -> Dict:
        """
        Get information about the collection

        Returns:
            Dictionary with collection information
        """
        count = self.collection.count()
        return {
            'name': self.collection_name,
            'count': count,
            'persist_directory': self.persist_directory
        }
