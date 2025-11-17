"""File tracker to manage processed files and avoid reprocessing"""
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple


class FileTracker:
    """Track processed files to enable incremental processing"""

    def __init__(self, tracking_file: str = "data/processed_files.json"):
        """
        Initialize file tracker

        Args:
            tracking_file: Path to JSON file for tracking processed files
        """
        self.tracking_file = tracking_file
        self.processed_files = self._load_tracking_data()

    def _load_tracking_data(self) -> Dict:
        """Load tracking data from JSON file"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Warning: Could not load tracking file: {e}")
                return {}
        return {}

    def _save_tracking_data(self):
        """Save tracking data to JSON file"""
        os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_files, f, indent=2, ensure_ascii=False)

    def _get_file_info(self, file_path: str) -> Dict:
        """
        Get file metadata

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'modified_time': stat.st_mtime,
            'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

    def _get_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of file content

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def is_processed(self, file_path: str) -> bool:
        """
        Check if file has been processed and hasn't changed

        Args:
            file_path: Path to file

        Returns:
            True if file is already processed and unchanged
        """
        filename = os.path.basename(file_path)

        # File not in tracking data
        if filename not in self.processed_files:
            return False

        # Get current file info
        try:
            current_info = self._get_file_info(file_path)
        except OSError:
            return False

        # Get stored file info
        stored_info = self.processed_files[filename]

        # Check if file has changed (size or modified time)
        if (current_info['size'] != stored_info.get('size') or
            current_info['modified_time'] != stored_info.get('modified_time')):
            return False

        return True

    def is_updated(self, file_path: str) -> bool:
        """
        Check if file has been processed before but has been updated

        Args:
            file_path: Path to file

        Returns:
            True if file was processed before and has been modified
        """
        filename = os.path.basename(file_path)

        # File not in tracking data - not updated, it's new
        if filename not in self.processed_files:
            return False

        # Get current file info
        try:
            current_info = self._get_file_info(file_path)
        except OSError:
            return False

        # Get stored file info
        stored_info = self.processed_files[filename]

        # Check if file has changed (size or modified time)
        if (current_info['size'] != stored_info.get('size') or
            current_info['modified_time'] != stored_info.get('modified_time')):
            return True

        return False

    def mark_processed(self, file_path: str, chunks_count: int = 0):
        """
        Mark file as processed

        Args:
            file_path: Path to file
            chunks_count: Number of chunks created from this file
        """
        filename = os.path.basename(file_path)
        file_info = self._get_file_info(file_path)
        file_hash = self._get_file_hash(file_path)

        self.processed_files[filename] = {
            'size': file_info['size'],
            'modified_time': file_info['modified_time'],
            'modified_date': file_info['modified_date'],
            'processed_date': datetime.now().isoformat(),
            'chunks_count': chunks_count,
            'content_hash': file_hash
        }

        self._save_tracking_data()

    def get_processed_info(self, file_path: str) -> Optional[Dict]:
        """
        Get processing information for a file

        Args:
            file_path: Path to file

        Returns:
            Processing info dictionary or None if not processed
        """
        filename = os.path.basename(file_path)
        return self.processed_files.get(filename)

    def clear_tracking(self):
        """Clear all tracking data"""
        self.processed_files = {}
        self._save_tracking_data()
        print("✓ Cleared all file tracking data")

    def remove_file(self, file_path: str):
        """
        Remove file from tracking

        Args:
            file_path: Path to file
        """
        filename = os.path.basename(file_path)
        if filename in self.processed_files:
            del self.processed_files[filename]
            self._save_tracking_data()

    def get_stats(self) -> Dict:
        """
        Get tracking statistics

        Returns:
            Dictionary with statistics
        """
        total_files = len(self.processed_files)
        total_chunks = sum(info.get('chunks_count', 0)
                          for info in self.processed_files.values())

        return {
            'total_files': total_files,
            'total_chunks': total_chunks,
            'tracking_file': self.tracking_file
        }

    def find_duplicate_by_hash(self, file_path: str) -> Optional[Tuple[str, str]]:
        """
        Check if a file with the same content hash already exists

        Args:
            file_path: Path to file to check

        Returns:
            Tuple of (duplicate_filename, file_extension) if duplicate found, None otherwise
        """
        try:
            current_hash = self._get_file_hash(file_path)
            current_filename = os.path.basename(file_path)

            # Search for files with same hash
            for filename, info in self.processed_files.items():
                # Skip the file itself
                if filename == current_filename:
                    continue

                # Check if hash matches
                if info.get('content_hash') == current_hash:
                    # Get file extension
                    ext = os.path.splitext(filename)[1]
                    return (filename, ext)

            return None

        except Exception as e:
            print(f"⚠️  Warning: Could not check for duplicates: {e}")
            return None
