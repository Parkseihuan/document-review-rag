"""Test script for file update detection and handling"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import FileTracker


def test_file_update_detection():
    """Test file update detection functionality"""
    print("=" * 60)
    print("Testing File Update Detection")
    print("=" * 60)

    # Use a test tracking file
    test_tracker = FileTracker(tracking_file="data/test_update_tracking.json")

    # Create a test file
    test_file = "data/test_update_file.txt"
    os.makedirs("data", exist_ok=True)
    with open(test_file, 'w') as f:
        f.write("Version 1 of the file")

    print("\n1. Initial state:")
    print(f"   is_processed: {test_tracker.is_processed(test_file)}")
    print(f"   is_updated: {test_tracker.is_updated(test_file)}")
    assert not test_tracker.is_processed(test_file), "New file should not be processed"
    assert not test_tracker.is_updated(test_file), "New file should not be updated"
    print("   ✓ Correct - file is new")

    print("\n2. After marking as processed:")
    test_tracker.mark_processed(test_file, chunks_count=10)
    print(f"   is_processed: {test_tracker.is_processed(test_file)}")
    print(f"   is_updated: {test_tracker.is_updated(test_file)}")
    assert test_tracker.is_processed(test_file), "Marked file should be processed"
    assert not test_tracker.is_updated(test_file), "Unchanged file should not be updated"
    print("   ✓ Correct - file is processed and unchanged")

    print("\n3. After modifying the file:")
    time.sleep(0.1)  # Ensure modification time changes
    with open(test_file, 'a') as f:
        f.write("\nVersion 2 - Added new content")

    print(f"   is_processed: {test_tracker.is_processed(test_file)}")
    print(f"   is_updated: {test_tracker.is_updated(test_file)}")
    assert not test_tracker.is_processed(test_file), "Modified file should not be 'processed'"
    assert test_tracker.is_updated(test_file), "Modified file should be detected as 'updated'"
    print("   ✓ Correct - file change detected!")

    print("\n4. After marking updated file as processed:")
    test_tracker.mark_processed(test_file, chunks_count=12)
    print(f"   is_processed: {test_tracker.is_processed(test_file)}")
    print(f"   is_updated: {test_tracker.is_updated(test_file)}")
    assert test_tracker.is_processed(test_file), "Re-marked file should be processed"
    assert not test_tracker.is_updated(test_file), "Re-marked file should not be 'updated'"
    print("   ✓ Correct - updated version now tracked")

    # Cleanup
    os.remove(test_file)
    if os.path.exists("data/test_update_tracking.json"):
        os.remove("data/test_update_tracking.json")

    print("\n" + "=" * 60)
    print("✓ All file update detection tests passed!")
    print("=" * 60)

    print("\n📝 Summary:")
    print("- ✅ New files: is_processed=False, is_updated=False")
    print("- ✅ Processed files: is_processed=True, is_updated=False")
    print("- ✅ Modified files: is_processed=False, is_updated=True")
    print("- ✅ Re-processed updates: is_processed=True, is_updated=False")


if __name__ == "__main__":
    test_file_update_detection()
