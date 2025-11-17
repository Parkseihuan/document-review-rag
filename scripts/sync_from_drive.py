"""Sync documents from Google Drive folders"""
import sys
import os
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.google_drive import GoogleDriveConnector
from src.vector_store import ChromaStore
from src.utils import FileTracker


def delete_local_file(filename):
    """
    Delete a file from RAG system (ChromaDB, tracking, markdown, raw)

    Args:
        filename: Name of the file to delete

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # 1. Delete from ChromaDB
        vector_store = ChromaStore(
            persist_directory=Config.CHROMA_DB_PATH,
            collection_name="documents"
        )

        # Try both filename and .md version
        deleted_count = vector_store.delete_by_source(filename)
        md_filename = os.path.splitext(filename)[0] + '.md'
        if deleted_count == 0:
            deleted_count = vector_store.delete_by_source(md_filename)

        # 2. Delete from file tracker
        file_tracker = FileTracker()
        raw_path = os.path.join(Config.RAW_DATA_DIR, filename)
        file_tracker.remove_file(raw_path)

        # 3. Delete markdown file
        md_path = os.path.join(Config.MARKDOWN_DIR, md_filename)
        if os.path.exists(md_path):
            os.remove(md_path)

        # 4. Delete raw file
        if os.path.exists(raw_path):
            os.remove(raw_path)

        return True

    except Exception as e:
        print(f"      ⚠️  Error deleting {filename}: {e}")
        return False


def sync_deletions(connector, folder_ids, auto_delete=False):
    """
    Sync deletions from Drive to local RAG system

    Args:
        connector: GoogleDriveConnector instance
        folder_ids: List of Drive folder IDs
        auto_delete: If True, delete without confirmation

    Returns:
        int: Number of files deleted
    """
    print(f"\n{'='*60}")
    print("Checking for deleted files...")
    print(f"{'='*60}")

    # Get all files from all Drive folders
    drive_files = set()
    for folder_id in folder_ids:
        try:
            files = connector.list_files(
                folder_id=folder_id,
                file_types=Config.SUPPORTED_EXTENSIONS
            )
            for file in files:
                drive_files.add(file['name'])
        except Exception as e:
            print(f"⚠️  Warning: Could not list files in folder {folder_id}: {e}")
            continue

    print(f"   📁 Files in Drive: {len(drive_files)}")

    # Get all local raw files
    local_files = set()
    if os.path.exists(Config.RAW_DATA_DIR):
        for filename in os.listdir(Config.RAW_DATA_DIR):
            file_path = os.path.join(Config.RAW_DATA_DIR, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in Config.SUPPORTED_EXTENSIONS:
                    local_files.add(filename)

    print(f"   💾 Files locally: {len(local_files)}")

    # Find deleted files (in local but not in Drive)
    deleted_files = local_files - drive_files

    if not deleted_files:
        print(f"\n   ✓ No files to delete")
        return 0

    print(f"\n   🗑️  Found {len(deleted_files)} deleted files:")
    for filename in sorted(deleted_files):
        print(f"      - {filename}")

    # Ask for confirmation (unless auto_delete is True)
    if not auto_delete:
        print(f"\n⚠️  These files will be deleted from RAG system:")
        print(f"   - ChromaDB (all chunks)")
        print(f"   - File tracking")
        print(f"   - Markdown files")
        print(f"   - Raw files")

        response = input(f"\n   Delete {len(deleted_files)} files? [y/N]: ").strip().lower()

        if response != 'y':
            print(f"   ❌ Deletion cancelled")
            return 0

    # Delete files
    print(f"\n   Deleting files...")
    deleted_count = 0
    for filename in sorted(deleted_files):
        print(f"      Deleting {filename}...")
        if delete_local_file(filename):
            deleted_count += 1
            print(f"      ✓ Deleted")
        else:
            print(f"      ❌ Failed")

    return deleted_count


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Sync documents from Google Drive')
    parser.add_argument('--sync-deletions', action='store_true',
                       help='Sync deletions from Drive (delete local files not in Drive)')
    parser.add_argument('--auto-delete', action='store_true',
                       help='Automatically delete without confirmation (use with --sync-deletions)')
    args = parser.parse_args()

    print("=" * 60)
    print("Google Drive Sync")
    if args.sync_deletions:
        print("Mode: DOWNLOAD + DELETION SYNC")
    else:
        print("Mode: DOWNLOAD ONLY")
    print("=" * 60)

    # Get folder IDs
    folder_ids = Config.get_drive_folder_ids()

    if not folder_ids:
        print("\n❌ No Drive folder IDs configured")
        print("Please set GOOGLE_DRIVE_FOLDER_IDS in .env file")
        print("\nExample:")
        print("GOOGLE_DRIVE_FOLDER_IDS=folder1_id,folder2_id,folder3_id")
        return

    print(f"\n📁 Configured folders: {len(folder_ids)}")
    print(f"   - 내부결재문서")
    print(f"   - 상위법")
    print(f"   - 규정집")

    # Check credentials
    if not os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
        print(f"\n❌ Credentials file not found: {Config.GOOGLE_APPLICATION_CREDENTIALS}")
        print("\nPlease follow the setup guide to get credentials.json")
        return

    # Initialize Drive connector
    try:
        connector = GoogleDriveConnector(Config.GOOGLE_APPLICATION_CREDENTIALS)
        print(f"\n✓ Connected to Google Drive")
    except Exception as e:
        print(f"\n❌ Failed to connect to Google Drive: {e}")
        return

    # Ensure raw directory exists
    os.makedirs(Config.RAW_DATA_DIR, exist_ok=True)

    # Download from each folder
    print(f"\n{'='*60}")
    print("Downloading files...")
    print(f"{'='*60}")

    total_downloaded = 0

    for i, folder_id in enumerate(folder_ids, 1):
        folder_names = ['내부결재문서', '상위법', '규정집']
        folder_name = folder_names[i-1] if i <= len(folder_names) else f'Folder {i}'

        print(f"\n[{i}/{len(folder_ids)}] {folder_name}")
        print(f"Folder ID: {folder_id}")

        try:
            downloaded_files = connector.download_folder(
                folder_id=folder_id,
                destination_dir=Config.RAW_DATA_DIR,
                file_types=Config.SUPPORTED_EXTENSIONS
            )

            print(f"   ✓ Downloaded {len(downloaded_files)} files")
            total_downloaded += len(downloaded_files)

            # Show downloaded file names
            if downloaded_files:
                for file in downloaded_files[:5]:  # Show first 5
                    print(f"      - {file}")
                if len(downloaded_files) > 5:
                    print(f"      ... and {len(downloaded_files) - 5} more")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    # Summary
    print(f"\n{'='*60}")
    print("Download Complete!")
    print(f"{'='*60}")
    print(f"Total files downloaded: {total_downloaded}")
    print(f"Destination: {Config.RAW_DATA_DIR}")

    # Sync deletions if requested
    deleted_count = 0
    if args.sync_deletions:
        deleted_count = sync_deletions(connector, folder_ids, auto_delete=args.auto_delete)
        print(f"\n{'='*60}")
        print("Deletion Sync Complete!")
        print(f"{'='*60}")
        print(f"Files deleted: {deleted_count}")

    # Final summary
    print(f"\n{'='*60}")
    print("Sync Summary")
    print(f"{'='*60}")
    print(f"✓ Downloaded: {total_downloaded} files")
    print(f"✓ Deleted: {deleted_count} files")

    if total_downloaded > 0 or deleted_count > 0:
        print(f"\n📝 Next step:")
        print(f"   python scripts/process_documents.py")
        print(f"\n   Or use one-command automation:")
        print(f"   python scripts/sync_and_deploy.py")
    else:
        print(f"\nℹ️  No changes detected")

    # Show usage tip if not syncing deletions
    if not args.sync_deletions:
        print(f"\n💡 Tip: Use --sync-deletions to remove files deleted from Drive")
        print(f"   python scripts/sync_from_drive.py --sync-deletions")


if __name__ == "__main__":
    main()
