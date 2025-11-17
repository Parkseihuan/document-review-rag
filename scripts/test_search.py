"""Test script for searching the vector store"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.embeddings import GeminiEmbedder
from src.vector_store import ChromaStore


def main():
    """Test search functionality"""
    print("=" * 60)
    print("RAG Search Test")
    print("=" * 60)

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        return

    # Initialize services
    print("\nInitializing services...")
    embedder = GeminiEmbedder(api_key=Config.GOOGLE_API_KEY)
    vector_store = ChromaStore(
        persist_directory=Config.CHROMA_DB_PATH,
        collection_name="documents"
    )

    # Show collection info
    info = vector_store.get_collection_info()
    print(f"\nVector Store: {info['name']}")
    print(f"Total Documents: {info['count']}")

    if info['count'] == 0:
        print("\n✗ No documents in vector store.")
        print("Please run 'python scripts/process_documents.py' first.")
        return

    # Interactive search
    print("\n" + "=" * 60)
    print("Enter your search queries (type 'quit' to exit)")
    print("=" * 60)

    while True:
        query = input("\nQuery: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not query:
            continue

        print("\nSearching...")
        query_embedding = embedder.embed_query(query)

        if not query_embedding:
            print("✗ Failed to generate query embedding")
            continue

        results = vector_store.search(query_embedding, top_k=3)

        print(f"\n{'='*60}")
        print(f"Results for: {query}")
        print(f"{'='*60}")

        if not results['documents']:
            print("No results found.")
            continue

        for i, (doc, metadata, distance) in enumerate(
            zip(results['documents'], results['metadatas'], results['distances']),
            start=1
        ):
            score = 1 - distance
            print(f"\n[Result {i}] (Score: {score:.3f})")
            print(f"Source: {metadata.get('source', 'Unknown')}")
            print(f"Chunk: {metadata.get('chunk_index', '?')}/{metadata.get('total_chunks', '?')}")
            print(f"\nContent:\n{doc[:300]}...")
            print("-" * 60)


if __name__ == "__main__":
    main()
