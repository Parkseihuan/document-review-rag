"""Check for duplicate files in raw data directory"""
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.utils import FileTracker


def main():
    """Find and report duplicate files"""
    print("=" * 60)
    print("Duplicate File Checker")
    print("=" * 60)

    file_tracker = FileTracker()

    # Build hash map: hash -> list of filenames
    hash_map = defaultdict(list)

    print(f"\n📁 Scanning processed files...\n")

    for filename, info in file_tracker.processed_files.items():
        content_hash = info.get('content_hash')
        if content_hash:
            hash_map[content_hash].append({
                'filename': filename,
                'size': info.get('size', 0),
                'chunks': info.get('chunks_count', 0),
                'processed': info.get('processed_date', 'Unknown')
            })

    # Find duplicates (hashes with more than one file)
    duplicates = {h: files for h, files in hash_map.items() if len(files) > 1}

    if not duplicates:
        print("✓ No duplicate files found!")
        print("\nAll files have unique content.")
        return

    # Report duplicates
    print(f"⚠️  Found {len(duplicates)} groups of duplicate files:\n")

    for i, (content_hash, files) in enumerate(duplicates.items(), 1):
        print(f"Group {i}: {len(files)} files with identical content")
        print(f"Content Hash: {content_hash[:16]}...")
        print("-" * 50)

        for file_info in files:
            print(f"  📄 {file_info['filename']}")
            print(f"     Size: {file_info['size']:,} bytes")
            print(f"     Chunks: {file_info['chunks']}")
            print(f"     Processed: {file_info['processed']}")
            print()

    # Summary
    total_duplicate_files = sum(len(files) for files in duplicates.values())
    wasted_files = total_duplicate_files - len(duplicates)  # Extra copies

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Duplicate Groups: {len(duplicates)}")
    print(f"Total Duplicate Files: {total_duplicate_files}")
    print(f"Unnecessary Copies: {wasted_files}")
    print("\nRecommendation:")
    print("  Keep only one version of each duplicate group")
    print("  Delete others using: python scripts\\delete_document.py <filename>")
    print("=" * 60)


if __name__ == "__main__":
    main()
