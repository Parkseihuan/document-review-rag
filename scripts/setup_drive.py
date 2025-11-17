"""Setup script for Google Drive authentication"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.google_drive import GoogleDriveConnector
from config import Config


def main():
    """Setup Google Drive authentication"""
    print("=" * 50)
    print("Google Drive Setup")
    print("=" * 50)

    credentials_path = Config.GOOGLE_APPLICATION_CREDENTIALS

    if not os.path.exists(credentials_path):
        print(f"\n✗ Credentials file not found: {credentials_path}")
        print("\nPlease follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Drive API")
        print("4. Create credentials (OAuth 2.0 or Service Account)")
        print(f"5. Download and save as '{credentials_path}'")
        return

    try:
        print(f"\n✓ Credentials file found: {credentials_path}")
        print("\nAuthenticating with Google Drive...")

        connector = GoogleDriveConnector(credentials_path)

        print("\n✓ Authentication successful!")
        print("\nTesting file listing...")

        files = connector.list_files()
        print(f"\n✓ Found {len(files)} files in your Drive")

        if files:
            print("\nFirst 5 files:")
            for i, file in enumerate(files[:5], 1):
                print(f"  {i}. {file['name']}")

        print("\n" + "=" * 50)
        print("Setup complete! You can now use the document processor.")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        print("\nPlease check your credentials and try again.")


if __name__ == "__main__":
    main()
