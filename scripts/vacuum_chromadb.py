"""Vacuum ChromaDB to reduce file size"""
import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config


def get_file_size(filepath):
    """Get file size in MB"""
    if os.path.exists(filepath):
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    return 0


def main():
    print("=" * 60)
    print("ChromaDB VACUUM - File Size Optimization")
    print("=" * 60)

    # Find SQLite file
    db_path = os.path.join(Config.CHROMA_DB_PATH, "chroma.sqlite3")

    if not os.path.exists(db_path):
        print(f"\n❌ Database file not found: {db_path}")
        return

    # Show current size
    size_before = get_file_size(db_path)
    print(f"\n📊 Current file size: {size_before:.2f} MB")

    # Confirm
    print("\nVACUUM will:")
    print("  ✓ Remove deleted data permanently")
    print("  ✓ Reduce file size")
    print("  ✓ Optimize database performance")
    print("\n⚠️  This may take a few seconds...")

    response = input("\nContinue? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled")
        return

    # Perform VACUUM
    print("\n🔧 Running VACUUM...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        print("✓ VACUUM complete")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Show new size
    size_after = get_file_size(db_path)
    size_saved = size_before - size_after
    percent_saved = (size_saved / size_before * 100) if size_before > 0 else 0

    print("\n" + "=" * 60)
    print("Optimization Complete!")
    print("=" * 60)
    print(f"Before:  {size_before:.2f} MB")
    print(f"After:   {size_after:.2f} MB")
    print(f"Saved:   {size_saved:.2f} MB ({percent_saved:.1f}%)")
    print("\n✓ Database optimized successfully!")


if __name__ == "__main__":
    main()
