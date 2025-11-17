"""Gemini API embeddings generator"""
import google.generativeai as genai
from typing import List, Union
import time


class GeminiEmbedder:
    """Generate embeddings using Google Gemini API"""

    def __init__(self, api_key: str, model_name: str = "models/embedding-001"):
        """
        Initialize Gemini embedder

        Args:
            api_key: Google API key
            model_name: Gemini embedding model name
        """
        genai.configure(api_key=api_key)
        self.model_name = model_name

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def embed_texts(self, texts: List[str], batch_size: int = 100, delay: float = 0.1) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            delay: Delay between batches to avoid rate limiting

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}")

            for text in batch:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
                time.sleep(delay)  # Rate limiting

        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []
