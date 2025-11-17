"""Test script for file tracking functionality"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import FileTracker


def test_file_tracker():
    """Test file tracking functionality"""
    print("=" * 60)
    print("Testing File Tracker")
    print("=" * 60)

    # Use a test tracking file
    test_tracker = FileTracker(tracking_file="data/test_processed_files.json")

    # Create a test file
    test_file = "data/test_file.txt"
    os.makedirs("data", exist_ok=True)
    with open(test_file, 'w') as f:
        f.write("This is a test file for tracking")

    print("\n1. Testing file tracking:")
    print(f"   Is processed: {test_tracker.is_processed(test_file)}")
    assert not test_tracker.is_processed(test_file), "New file should not be processed"
    print("   ✓ New file correctly identified")

    print("\n2. Marking file as processed:")
    test_tracker.mark_processed(test_file, chunks_count=5)
    print(f"   Is processed: {test_tracker.is_processed(test_file)}")
    assert test_tracker.is_processed(test_file), "Marked file should be processed"
    print("   ✓ File correctly marked as processed")

    print("\n3. Getting file info:")
    info = test_tracker.get_processed_info(test_file)
    print(f"   Chunks: {info['chunks_count']}")
    print(f"   Processed: {info['processed_date']}")
    assert info['chunks_count'] == 5, "Chunk count should match"
    print("   ✓ File info correctly stored")

    print("\n4. Testing file change detection:")
    # Modify the file
    with open(test_file, 'a') as f:
        f.write("\nAdded new content")
    print(f"   Is processed after change: {test_tracker.is_processed(test_file)}")
    assert not test_tracker.is_processed(test_file), "Modified file should need reprocessing"
    print("   ✓ File change correctly detected")

    print("\n5. Testing stats:")
    stats = test_tracker.get_stats()
    print(f"   Total files: {stats['total_files']}")
    print(f"   Total chunks: {stats['total_chunks']}")
    print("   ✓ Stats working correctly")

    # Cleanup
    os.remove(test_file)
    if os.path.exists("data/test_processed_files.json"):
        os.remove("data/test_processed_files.json")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_file_tracker()
