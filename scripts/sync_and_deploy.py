"""One-command automation: Sync from Drive → Process → Deploy to Cloud Run"""
import sys
import os
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config


def run_command(description, command, critical=True):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} - Complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        if critical:
            print(f"\nError: {e}")
            print("\nStopping automation due to critical error")
            sys.exit(1)
        return False


def main():
    print("=" * 60)
    print("🚀 RAG Automation: Sync → Process → Deploy")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Download new files from Google Drive (3 folders)")
    print("  2. Sync deletions (remove files deleted from Drive)")
    print("  3. Parse documents (PDF, DOCX, HWP, TXT, XLSX)")
    print("  4. Chunk and embed documents")
    print("  5. Update ChromaDB")
    print("  6. Deploy to Cloud Run")
    print("\nEstimated time: 3-5 minutes")

    # Ask about deletion sync
    sync_deletions = input("\nSync deletions from Drive? (Y/n): ").strip().lower()
    sync_deletions = sync_deletions != 'n'  # Default to yes

    # Confirm
    response = input("\nContinue? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled")
        return

    # Step 1: Sync from Drive
    sync_command = "python scripts/sync_from_drive.py"
    if sync_deletions:
        sync_command += " --sync-deletions --auto-delete"

    success = run_command(
        "[1/6] 📥 Syncing from Google Drive",
        sync_command,
        critical=False  # Don't stop if no new files
    )

    # Step 2: Process documents
    run_command(
        "[2/6] 📄 Processing documents",
        "python scripts/process_documents.py",
        critical=True
    )

    # Step 3: Commit to git
    print(f"\n{'='*60}")
    print("[3/6] 💾 Committing changes to Git")
    print(f"{'='*60}")

    # Check if there are changes
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        run_command(
            "Adding changes",
            "git add data/vector_db data/processed_files.json data/markdown",
            critical=False
        )

        # Create commit message
        commit_msg = input("\nEnter commit message (or press Enter for default): ").strip()
        if not commit_msg:
            commit_msg = "Update RAG documents from Google Drive"

        run_command(
            "Committing changes",
            f'git commit -m "{commit_msg}"',
            critical=False
        )

        run_command(
            "Pushing to GitHub",
            "git push",
            critical=False
        )
    else:
        print("   ℹ️  No changes to commit")

    # Step 4: Deploy to Cloud Run (optional)
    print(f"\n{'='*60}")
    print("[4/6] 🚀 Deploy to Cloud Run?")
    print(f"{'='*60}")

    deploy = input("Deploy to Cloud Run? (y/N): ").strip().lower()

    if deploy == 'y':
        region = input("Enter region (default: asia-northeast3): ").strip()
        if not region:
            region = "asia-northeast3"

        run_command(
            "[5/6] Deploying to Cloud Run",
            f"gcloud run deploy rag-api --source . --region {region} --allow-unauthenticated",
            critical=False
        )
    else:
        print("   ⏭️  Skipped Cloud Run deployment")
        print("   ℹ️  Run manually: gcloud run deploy rag-api --source . --region asia-northeast3")

    # Step 5: Summary
    print(f"\n{'='*60}")
    print("[6/6] 🎉 Automation Complete!")
    print(f"{'='*60}")

    # Show stats
    try:
        from src.vector_store import ChromaStore
        vector_store = ChromaStore(
            persist_directory=Config.CHROMA_DB_PATH,
            collection_name="documents"
        )
        info = vector_store.get_collection_info()
        print(f"\nVector DB Status:")
        print(f"  Total documents: {info['count']}")
        print(f"  Location: {info['persist_directory']}")
    except:
        pass

    print(f"\n📝 Next steps:")
    print(f"  1. Test chatbot: https://parkseihuan.github.io/chatbot-gyomu/")
    print(f"  2. Check RAG API: https://rag-api-xxxxx.run.app/info")
    print(f"  3. View logs: gcloud run services logs read rag-api")


if __name__ == "__main__":
    main()
