"""Script to delete documents from the RAG system"""
import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.vector_store import ChromaStore
from src.utils import FileTracker


def list_documents():
    """List all documents in the system"""
    print("=" * 60)
    print("Documents in RAG System")
    print("=" * 60)

    # Check raw folder
    raw_files = []
    if os.path.exists(Config.RAW_DATA_DIR):
        for filename in os.listdir(Config.RAW_DATA_DIR):
            file_path = os.path.join(Config.RAW_DATA_DIR, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in Config.SUPPORTED_EXTENSIONS:
                    raw_files.append(filename)

    print(f"\n📁 Raw files ({len(raw_files)}):")
    for filename in sorted(raw_files):
        print(f"  - {filename}")

    # Check ChromaDB
    vector_store = ChromaStore(
        persist_directory=Config.CHROMA_DB_PATH,
        collection_name="documents"
    )

    all_data = vector_store.collection.get()
    source_counts = {}
    for metadata in all_data['metadatas']:
        source = metadata.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1

    print(f"\n🗄️  ChromaDB documents ({len(source_counts)} files, {len(all_data['ids'])} chunks):")
    for source in sorted(source_counts.keys()):
        count = source_counts[source]
        print(f"  - {source} ({count} chunks)")

    # Check tracking
    file_tracker = FileTracker()
    stats = file_tracker.get_stats()

    print(f"\n📊 Tracked files: {stats['total_files']}")

    return raw_files, source_counts


def delete_document(filename, delete_raw=True):
    """
    Delete a document from the RAG system

    Args:
        filename: Name of the file to delete
        delete_raw: Whether to delete the raw file
    """
    print("\n" + "=" * 60)
    print(f"Deleting: {filename}")
    print("=" * 60)

    deleted_items = []

    # 1. Delete from ChromaDB
    print("\n[1/4] Deleting from ChromaDB...")
    vector_store = ChromaStore(
        persist_directory=Config.CHROMA_DB_PATH,
        collection_name="documents"
    )

    # Delete by source (filename or .md version)
    base_name = os.path.splitext(filename)[0]
    md_filename = base_name + '.md'

    deleted_count = vector_store.delete_by_source(filename)
    if deleted_count == 0:
        # Try .md version
        deleted_count = vector_store.delete_by_source(md_filename)

    if deleted_count > 0:
        deleted_items.append(f"ChromaDB: {deleted_count} chunks")
    else:
        print("  ⚠️  No chunks found in ChromaDB")

    # 2. Delete from file tracker
    print("\n[2/4] Deleting from file tracker...")
    file_tracker = FileTracker()
    raw_path = os.path.join(Config.RAW_DATA_DIR, filename)

    info = file_tracker.get_processed_info(raw_path)
    if info:
        file_tracker.remove_file(raw_path)
        deleted_items.append(f"Tracking: {filename}")
    else:
        print("  ⚠️  Not found in tracking data")

    # 3. Delete markdown file
    print("\n[3/4] Deleting markdown file...")
    md_path = os.path.join(Config.MARKDOWN_DIR, md_filename)
    if os.path.exists(md_path):
        os.remove(md_path)
        deleted_items.append(f"Markdown: {md_filename}")
        print(f"  ✓ Deleted {md_filename}")
    else:
        print("  ⚠️  Markdown file not found")

    # 4. Delete raw file (if requested)
    if delete_raw:
        print("\n[4/4] Deleting raw file...")
        if os.path.exists(raw_path):
            os.remove(raw_path)
            deleted_items.append(f"Raw file: {filename}")
            print(f"  ✓ Deleted {filename}")
        else:
            print("  ⚠️  Raw file not found")
    else:
        print("\n[4/4] Keeping raw file (--keep-raw specified)")

    # Summary
    print("\n" + "=" * 60)
    print("Deletion Summary")
    print("=" * 60)
    if deleted_items:
        for item in deleted_items:
            print(f"✓ {item}")
        print(f"\n✅ Successfully deleted {len(deleted_items)} items")
    else:
        print("⚠️  No items were deleted")


def main():
    parser = argparse.ArgumentParser(description='Delete documents from RAG system')
    parser.add_argument('--list', action='store_true',
                       help='List all documents in the system')
    parser.add_argument('--delete', type=str,
                       help='Delete a specific document (filename)')
    parser.add_argument('--keep-raw', action='store_true',
                       help='Keep the raw file (only delete from ChromaDB and tracking)')

    args = parser.parse_args()

    if args.list or not args.delete:
        list_documents()

    if args.delete:
        print()
        response = input(f"⚠️  Are you sure you want to delete '{args.delete}'? (yes/no): ").strip().lower()
        if response == 'yes':
            delete_document(args.delete, delete_raw=not args.keep_raw)
        else:
            print("\n❌ Deletion cancelled")


if __name__ == "__main__":
    main()
