"""Configuration settings for RAG system"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Google Drive
    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')  # Legacy: single folder
    GOOGLE_DRIVE_FOLDER_IDS = os.getenv('GOOGLE_DRIVE_FOLDER_IDS', '')  # New: multiple folders
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')

    @classmethod
    def get_drive_folder_ids(cls):
        """Get list of Drive folder IDs"""
        # Support both single and multiple folders
        if cls.GOOGLE_DRIVE_FOLDER_IDS:
            return [fid.strip() for fid in cls.GOOGLE_DRIVE_FOLDER_IDS.split(',') if fid.strip()]
        elif cls.GOOGLE_DRIVE_FOLDER_ID:
            return [cls.GOOGLE_DRIVE_FOLDER_ID]
        return []

    # Google Gemini API
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

    # ChromaDB
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './data/vector_db')

    # API Server
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))

    # Processing
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))

    # Directories
    RAW_DATA_DIR = './data/raw'
    MARKDOWN_DIR = './data/markdown'

    # Supported file extensions
    SUPPORTED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.md']

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = {
            'GOOGLE_API_KEY': cls.GOOGLE_API_KEY,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        return True
