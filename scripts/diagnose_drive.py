"""Diagnose Google Drive folder contents"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from src.google_drive import GoogleDriveConnector


def main():
    print("=" * 60)
    print("Google Drive Diagnosis")
    print("=" * 60)

    # Get folder IDs
    folder_ids = Config.get_drive_folder_ids()

    if not folder_ids:
        print("❌ No folder IDs configured")
        return

    # Initialize Drive
    try:
        connector = GoogleDriveConnector(Config.GOOGLE_APPLICATION_CREDENTIALS)
        print("✓ Connected to Google Drive\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    folder_names = ['내부결재문서', '상위법', '규정집']

    for i, folder_id in enumerate(folder_ids):
        folder_name = folder_names[i] if i < len(folder_names) else f'Folder {i+1}'

        print("=" * 60)
        print(f"[{i+1}/3] {folder_name}")
        print(f"Folder ID: {folder_id}")
        print("=" * 60)

        try:
            # List ALL files (no filter)
            print("\n📁 모든 파일:")
            all_files = connector.list_files(folder_id=folder_id, file_types=None)

            if not all_files:
                print("   ⚠️  폴더가 비어있거나 접근 권한이 없습니다")
                print("\n   확인사항:")
                print("   1. Drive 폴더에 실제로 파일이 있나요?")
                print("   2. Service Account와 폴더가 공유되어 있나요?")
                print(f"   3. Service Account 이메일 확인:")

                # Show service account email
                import json
                if os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
                    with open(Config.GOOGLE_APPLICATION_CREDENTIALS, 'r') as f:
                        creds_data = json.load(f)
                        print(f"      {creds_data.get('client_email', 'Unknown')}")
                continue

            print(f"   총 {len(all_files)}개 파일 발견\n")

            # Show all files
            for idx, file in enumerate(all_files, 1):
                name = file.get('name', 'Unknown')
                mime = file.get('mimeType', 'Unknown')
                size = file.get('size', 0)

                # Check if supported
                ext = os.path.splitext(name)[1].lower()
                supported = ext in ['.pdf', '.docx', '.hwp']
                status = "✅ 지원됨" if supported else "❌ 미지원"

                print(f"   [{idx}] {name}")
                print(f"       타입: {mime}")
                print(f"       크기: {int(size):,} bytes" if size else "       크기: Unknown")
                print(f"       상태: {status}")
                print()

            # List supported files only
            print("\n📄 지원되는 파일 (.pdf, .docx, .hwp):")
            supported_files = connector.list_files(
                folder_id=folder_id,
                file_types=['.pdf', '.docx', '.hwp']
            )

            if supported_files:
                print(f"   총 {len(supported_files)}개\n")
                for idx, file in enumerate(supported_files, 1):
                    print(f"   [{idx}] {file.get('name')}")
            else:
                print("   ⚠️  지원되는 파일이 없습니다")
                print("   폴더에 PDF, DOCX, HWP 파일을 업로드하세요")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("=" * 60)
    print("진단 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
