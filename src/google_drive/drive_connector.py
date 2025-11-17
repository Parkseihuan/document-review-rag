"""Google Drive API connector for downloading documents"""
import os
import io
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pickle


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class GoogleDriveConnector:
    """Connects to Google Drive and downloads documents"""

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.pickle'):
        """
        Initialize Google Drive connector

        Args:
            credentials_path: Path to Google API credentials JSON
            token_path: Path to save/load user token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None

        # Check for existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Try service account first
                if os.path.exists(self.credentials_path):
                    try:
                        creds = service_account.Credentials.from_service_account_file(
                            self.credentials_path, scopes=SCOPES
                        )
                    except Exception:
                        # Fall back to OAuth flow
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, SCOPES
                        )
                        creds = flow.run_local_server(port=0)

                # Save credentials
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)

    def list_files(self, folder_id: Optional[str] = None, file_types: List[str] = None) -> List[Dict]:
        """
        List files in Google Drive folder

        Args:
            folder_id: Google Drive folder ID (None for all files)
            file_types: List of file extensions to filter (e.g., ['.pdf', '.docx'])

        Returns:
            List of file metadata dictionaries
        """
        query_parts = []

        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")

        if file_types:
            # Convert extensions to mimeType queries
            mime_types = []
            for ext in file_types:
                if ext == '.pdf':
                    mime_types.append("mimeType='application/pdf'")
                elif ext == '.doc':
                    mime_types.append("mimeType='application/msword'")
                elif ext == '.docx':
                    mime_types.append("mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'")
                elif ext == '.txt':
                    mime_types.append("mimeType='text/plain'")
                elif ext == '.xlsx':
                    mime_types.append("mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'")
                elif ext == '.md':
                    mime_types.append("mimeType='text/markdown'")
                    mime_types.append("mimeType='text/plain'")  # Sometimes MD files are marked as plain text

            if mime_types:
                query_parts.append(f"({' or '.join(mime_types)})")

        query_parts.append("trashed=false")
        query = ' and '.join(query_parts) if query_parts else None

        results = []
        page_token = None

        while True:
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, modifiedTime, size)',
                pageToken=page_token
            ).execute()

            results.extend(response.get('files', []))
            page_token = response.get('nextPageToken')

            if not page_token:
                break

        return results

    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download a file from Google Drive

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save the file

        Returns:
            True if download successful, False otherwise
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_handle = io.BytesIO()

            downloader = MediaIoBaseDownload(file_handle, request)
            done = False

            while not done:
                status, done = downloader.next_chunk()

            # Save to file
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            with open(destination_path, 'wb') as f:
                f.write(file_handle.getvalue())

            return True

        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return False

    def download_folder(self, folder_id: str, destination_dir: str, file_types: List[str] = None) -> List[str]:
        """
        Download all files from a Google Drive folder

        Args:
            folder_id: Google Drive folder ID
            destination_dir: Local directory to save files
            file_types: List of file extensions to download

        Returns:
            List of downloaded file paths
        """
        files = self.list_files(folder_id, file_types)
        downloaded_files = []

        os.makedirs(destination_dir, exist_ok=True)

        for file in files:
            file_name = file['name']
            file_id = file['id']
            destination_path = os.path.join(destination_dir, file_name)

            print(f"Downloading: {file_name}")
            if self.download_file(file_id, destination_path):
                downloaded_files.append(destination_path)
                print(f"✓ Downloaded: {file_name}")
            else:
                print(f"✗ Failed: {file_name}")

        return downloaded_files
