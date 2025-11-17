"""Script to inspect ChromaDB contents and search quality"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.vector_store import ChromaStore
from src.embeddings import GeminiEmbedder


def main():
    print("=" * 60)
    print("ChromaDB Inspector")
    print("=" * 60)

    # Initialize vector store
    vector_store = ChromaStore(
        persist_directory=Config.CHROMA_DB_PATH,
        collection_name="documents"
    )

    # Get collection info
    info = vector_store.get_collection_info()
    print(f"\nTotal documents in ChromaDB: {info['count']}")
    print(f"Location: {info['persist_directory']}")

    # Get all documents and group by source
    print("\n" + "=" * 60)
    print("Documents by Source File")
    print("=" * 60)

    all_data = vector_store.collection.get()

    # Group by source
    source_counts = {}
    for metadata in all_data['metadatas']:
        source = metadata.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1

    # Sort by count
    sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)

    for source, count in sorted_sources:
        print(f"{count:4d} chunks - {source}")

    print(f"\nTotal unique files: {len(source_counts)}")

    # Test search
    print("\n" + "=" * 60)
    print("Test Search: '연구년 신청 자격'")
    print("=" * 60)

    Config.validate()
    embedder = GeminiEmbedder(api_key=Config.GOOGLE_API_KEY)

    query = "연구년 신청 자격"
    query_embedding = embedder.embed_text(query)

    print(f"\nSearching with top_k=10...")
    results = vector_store.search(query_embedding, top_k=10)

    print(f"\nFound {len(results['documents'])} results:")
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'],
        results['metadatas'],
        results['distances']
    ), 1):
        print(f"\n[{i}] Source: {metadata.get('source', 'unknown')}")
        print(f"    Distance: {distance:.4f} (lower is better)")
        print(f"    Preview: {doc[:200]}...")


if __name__ == "__main__":
    main()
