"""Main script to process documents from Google Drive to vector store"""
import sys
import os
import argparse
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.google_drive import GoogleDriveConnector
from src.parsers import PDFParser, DOCParser, DOCXParser, TXTParser, XLSXParser, MDParser
from src.chunking import TextChunker
from src.embeddings import GeminiEmbedder
from src.vector_store import ChromaStore
from src.utils import FileTracker


def main():
    """Main processing pipeline"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process documents for RAG system')
    parser.add_argument('--force', action='store_true',
                       help='Force reprocessing of all files (ignore tracking)')
    parser.add_argument('--clear-tracking', action='store_true',
                       help='Clear file tracking data and exit')
    args = parser.parse_args()

    print("=" * 60)
    print("Document RAG Pipeline")
    if args.force:
        print("Mode: FORCE REPROCESS ALL FILES")
    else:
        print("Mode: INCREMENTAL (process new/changed files only)")
    print("=" * 60)

    # Initialize file tracker
    file_tracker = FileTracker()

    # Handle clear tracking command
    if args.clear_tracking:
        file_tracker.clear_tracking()
        print("\n✓ File tracking data cleared")
        return

    # Show tracking stats
    stats = file_tracker.get_stats()
    if stats['total_files'] > 0:
        print(f"\n📊 Previously processed: {stats['total_files']} files, {stats['total_chunks']} chunks")

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        return

    # Step 1: Download files from Google Drive (if folder ID provided)
    if Config.GOOGLE_DRIVE_FOLDER_ID:
        print("\n[1/5] Downloading files from Google Drive...")
        try:
            connector = GoogleDriveConnector(Config.GOOGLE_APPLICATION_CREDENTIALS)
            downloaded_files = connector.download_folder(
                folder_id=Config.GOOGLE_DRIVE_FOLDER_ID,
                destination_dir=Config.RAW_DATA_DIR,
                file_types=Config.SUPPORTED_EXTENSIONS
            )
            print(f"✓ Downloaded {len(downloaded_files)} files")
        except Exception as e:
            print(f"✗ Error downloading files: {e}")
            return
    else:
        print("\n[1/5] Skipping Google Drive download (no folder ID configured)")
        print(f"Looking for files in {Config.RAW_DATA_DIR}")

    # Step 2: Parse documents to markdown
    print("\n[2/5] Parsing documents to Markdown...")
    os.makedirs(Config.MARKDOWN_DIR, exist_ok=True)

    parsers = {
        '.pdf': PDFParser,
        '.doc': DOCParser,
        '.docx': DOCXParser,
        '.txt': TXTParser,
        '.xlsx': XLSXParser,
        '.md': MDParser
    }

    parsed_count = 0
    skipped_count = 0
    updated_count = 0
    duplicate_count = 0
    files_to_process = []  # Track which files we actually process
    files_to_update = []   # Track which files are being updated (need old chunks deleted)

    for filename in os.listdir(Config.RAW_DATA_DIR):
        file_path = os.path.join(Config.RAW_DATA_DIR, filename)
        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext in parsers:
            # Check if file should be skipped
            if not args.force and file_tracker.is_processed(file_path):
                print(f"  ⏭️  Skipping {filename} (already processed)")
                skipped_count += 1
                continue

            # Check for duplicate content (same content, different filename/extension)
            duplicate_info = file_tracker.find_duplicate_by_hash(file_path)
            if duplicate_info and not args.force:
                duplicate_filename, duplicate_ext = duplicate_info
                print(f"  🔁 Skipping {filename} (duplicate of {duplicate_filename})")
                duplicate_count += 1
                skipped_count += 1
                continue

            # Check if this is an update to existing file
            is_update = file_tracker.is_updated(file_path)
            if is_update:
                print(f"  🔄 Updating {filename} (file changed)")
                updated_count += 1

            parser = parsers[ext]
            md_filename = os.path.splitext(filename)[0] + '.md'
            md_path = os.path.join(Config.MARKDOWN_DIR, md_filename)

            print(f"  Parsing {filename}...")
            if parser.to_markdown(file_path, md_path):
                parsed_count += 1
                files_to_process.append((file_path, md_path))
                if is_update:
                    files_to_update.append(filename)
                print(f"  ✓ Saved to {md_filename}")
            else:
                print(f"  ✗ Failed to parse {filename}")

    print(f"✓ Parsed {parsed_count} documents")
    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} already-processed documents")
    if duplicate_count > 0:
        print(f"🔁 Skipped {duplicate_count} duplicate files (same content, different format)")
    if updated_count > 0:
        print(f"🔄 Updated {updated_count} modified documents")

    if parsed_count == 0:
        if skipped_count > 0:
            print("\n✓ All files already processed. Nothing to do.")
            print("  Use --force to reprocess all files")
        else:
            print("\n✗ No documents were parsed. Exiting.")
        return

    # Step 3: Chunk documents
    print("\n[3/5] Chunking documents...")
    chunker = TextChunker(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )

    # Only chunk the newly processed markdown files
    chunks = []
    file_chunks_map = {}  # Track chunks per file for marking processed
    for raw_path, md_path in files_to_process:
        file_chunks = chunker.chunk_file(md_path)
        chunks.extend(file_chunks)
        file_chunks_map[raw_path] = len(file_chunks)
        print(f"  ✓ {os.path.basename(raw_path)}: {len(file_chunks)} chunks")

    print(f"✓ Created {len(chunks)} chunks from {parsed_count} documents")

    if not chunks:
        print("\n✗ No chunks created. Exiting.")
        return

    # Step 4: Generate embeddings
    print("\n[4/5] Generating embeddings with Gemini API...")
    embedder = GeminiEmbedder(api_key=Config.GOOGLE_API_KEY)

    texts = [chunk['text'] for chunk in chunks]
    embeddings = []

    for i, text in enumerate(tqdm(texts, desc="Embedding")):
        embedding = embedder.embed_text(text)
        embeddings.append(embedding)

        # Progress update every 10 chunks
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(texts)} chunks")

    print(f"✓ Generated {len(embeddings)} embeddings")

    # Check if embeddings are valid
    valid_embeddings = [emb for emb in embeddings if emb and len(emb) > 0]
    if len(valid_embeddings) == 0:
        print("\n" + "=" * 60)
        print("❌ ERROR: No valid embeddings were generated!")
        print("=" * 60)
        print("\nPossible causes:")
        print("1. API quota exceeded - check your Gemini API key")
        print("2. Invalid API key - verify your .env file")
        print("3. Network issues")
        print("\nPlease:")
        print("- Check .env file: type .env")
        print("- Verify API key at: https://makersuite.google.com/app/apikey")
        print("- Try with a different Google account")
        print("=" * 60)
        return

    if len(valid_embeddings) < len(embeddings):
        print(f"⚠️  Warning: Only {len(valid_embeddings)}/{len(embeddings)} embeddings are valid")
        print("Some chunks will be skipped")
        # Filter out invalid embeddings and corresponding chunks
        valid_data = [(chunk, emb) for chunk, emb in zip(chunks, embeddings) if emb and len(emb) > 0]
        chunks = [item[0] for item in valid_data]
        embeddings = [item[1] for item in valid_data]

    # Step 5: Store in ChromaDB
    print("\n[5/5] Storing in ChromaDB...")
    os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)
    vector_store = ChromaStore(
        persist_directory=Config.CHROMA_DB_PATH,
        collection_name="documents"
    )

    # Delete old chunks for updated files
    if files_to_update:
        print("\nRemoving old versions of updated files...")
        for filename in files_to_update:
            vector_store.delete_by_source(filename)

    vector_store.add_documents(chunks, embeddings)

    # Mark files as processed
    print("\n[6/6] Updating file tracking...")
    for raw_path in file_chunks_map:
        chunks_count = file_chunks_map[raw_path]
        file_tracker.mark_processed(raw_path, chunks_count)
        print(f"  ✓ Marked {os.path.basename(raw_path)} as processed")

    # Show summary
    info = vector_store.get_collection_info()
    tracking_stats = file_tracker.get_stats()

    print("\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Vector Store: {info['name']}")
    print(f"Total Documents in DB: {info['count']}")
    print(f"Location: {info['persist_directory']}")
    print(f"\nTracking Stats:")
    print(f"  Total Tracked Files: {tracking_stats['total_files']}")
    print(f"  Total Tracked Chunks: {tracking_stats['total_chunks']}")
    print(f"  Newly Processed: {parsed_count} files, {len(chunks)} chunks")
    print("\nYou can now start the API server with:")
    print("  python scripts/run_api_server.py")
    print("\nTo reprocess all files:")
    print("  python scripts/process_documents.py --force")
    print("=" * 60)


if __name__ == "__main__":
    main()
