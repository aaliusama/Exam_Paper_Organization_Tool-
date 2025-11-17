"""
Google Drive Uploader
Uploads parsed data to Google Drive
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriveUploader:
    """Upload files to Google Drive"""

    # Google Drive API scopes
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    # Target folder ID from the provided link
    # https://drive.google.com/drive/folders/1Gv3FJ7MiAicT1eA_B6MxfaA8ShrDlrki
    TARGET_FOLDER_ID = '1Gv3FJ7MiAicT1eA_B6MxfaA8ShrDlrki'

    def __init__(self, credentials_path: str = 'credentials.json',
                 token_path: str = 'token.json'):
        """
        Initialize Drive uploader

        Args:
            credentials_path: Path to OAuth2 credentials JSON
            token_path: Path to store access token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.folder_ids = {}  # Cache for created folders

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API

        Returns:
            True if authentication successful
        """
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            except Exception as e:
                logger.warning(f"Error loading token: {e}")

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    return False
            else:
                if not os.path.exists(self.credentials_path):
                    logger.error(f"Credentials file not found: {self.credentials_path}")
                    logger.info("Please download OAuth2 credentials from Google Cloud Console")
                    logger.info("and save as 'credentials.json'")
                    return False

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Authentication failed: {e}")
                    return False

            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        # Build service
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Drive")
            return True
        except Exception as e:
            logger.error(f"Failed to build Drive service: {e}")
            return False

    def create_folder(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        """
        Create a folder in Google Drive

        Args:
            folder_name: Name of folder to create
            parent_id: Parent folder ID (uses TARGET_FOLDER_ID if None)

        Returns:
            Folder ID if successful, None otherwise
        """
        if not self.service:
            logger.error("Not authenticated")
            return None

        # Use target folder as parent if not specified
        if parent_id is None:
            parent_id = self.TARGET_FOLDER_ID

        # Check cache
        cache_key = f"{parent_id}/{folder_name}"
        if cache_key in self.folder_ids:
            return self.folder_ids[cache_key]

        # Check if folder already exists
        try:
            query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])
            if files:
                folder_id = files[0]['id']
                logger.info(f"Folder already exists: {folder_name}")
                self.folder_ids[cache_key] = folder_id
                return folder_id

        except Exception as e:
            logger.warning(f"Error checking for existing folder: {e}")

        # Create new folder
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }

            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            folder_id = folder.get('id')
            self.folder_ids[cache_key] = folder_id
            logger.info(f"Created folder: {folder_name}")
            return folder_id

        except Exception as e:
            logger.error(f"Failed to create folder {folder_name}: {e}")
            return None

    def upload_file(self, file_path: Path, parent_folder_id: str = None,
                   remote_name: str = None) -> Optional[str]:
        """
        Upload a file to Google Drive

        Args:
            file_path: Local file path
            parent_folder_id: Parent folder ID (uses TARGET_FOLDER_ID if None)
            remote_name: Name for file in Drive (uses local name if None)

        Returns:
            File ID if successful, None otherwise
        """
        if not self.service:
            logger.error("Not authenticated")
            return None

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        # Use target folder as parent if not specified
        if parent_folder_id is None:
            parent_folder_id = self.TARGET_FOLDER_ID

        # Use original filename if remote name not specified
        if remote_name is None:
            remote_name = file_path.name

        try:
            # Determine MIME type
            mime_types = {
                '.json': 'application/json',
                '.csv': 'text/csv',
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
            }
            mime_type = mime_types.get(file_path.suffix, 'application/octet-stream')

            # File metadata
            file_metadata = {
                'name': remote_name,
                'parents': [parent_folder_id]
            }

            # Upload file
            media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = file.get('id')
            logger.info(f"✓ Uploaded: {remote_name}")
            return file_id

        except Exception as e:
            logger.error(f"Failed to upload {file_path.name}: {e}")
            return None

    def setup_folder_structure(self) -> Dict[str, str]:
        """
        Create the complete folder structure in Google Drive

        Returns:
            Dictionary mapping folder names to IDs
        """
        if not self.service:
            logger.error("Not authenticated")
            return {}

        logger.info("Setting up folder structure...")

        folders = {}

        # Main folder (already exists)
        folders['root'] = self.TARGET_FOLDER_ID

        # Create subfolders
        folder_names = ['raw_pdfs', 'parsed_json', 'combined_yearly_csv', 'master_dataset']

        for folder_name in folder_names:
            folder_id = self.create_folder(folder_name, self.TARGET_FOLDER_ID)
            if folder_id:
                folders[folder_name] = folder_id

        logger.info(f"Folder structure ready: {len(folders)} folders")
        return folders

    def upload_dataset(self, local_base_dir: str = "Cambridge-9709"):
        """
        Upload entire dataset to Google Drive

        Args:
            local_base_dir: Local base directory containing the dataset
        """
        if not self.service:
            logger.error("Not authenticated. Call authenticate() first.")
            return

        base_path = Path(local_base_dir)
        if not base_path.exists():
            logger.error(f"Directory not found: {base_path}")
            return

        # Setup folder structure
        folders = self.setup_folder_structure()

        logger.info("\n" + "="*60)
        logger.info("Starting upload to Google Drive")
        logger.info("="*60 + "\n")

        uploaded_count = 0

        # Upload folders
        folder_mappings = [
            ('parsed_json', 'parsed_json'),
            ('combined_yearly_csv', 'combined_yearly_csv'),
            ('master_dataset', 'master_dataset'),
        ]

        for local_folder, remote_folder_key in folder_mappings:
            local_path = base_path / local_folder
            if not local_path.exists():
                logger.warning(f"Folder not found: {local_path}")
                continue

            remote_folder_id = folders.get(remote_folder_key)
            if not remote_folder_id:
                logger.warning(f"Remote folder not found for: {remote_folder_key}")
                continue

            logger.info(f"\nUploading {local_folder}...")

            # Upload all files in folder
            for file_path in local_path.rglob('*'):
                if file_path.is_file():
                    if self.upload_file(file_path, remote_folder_id):
                        uploaded_count += 1

        # Upload raw PDFs (with year subfolders)
        raw_pdfs_path = base_path / 'raw_pdfs'
        if raw_pdfs_path.exists() and 'raw_pdfs' in folders:
            logger.info("\nUploading raw PDFs...")
            raw_pdfs_folder_id = folders['raw_pdfs']

            # Create year folders
            for year_folder in sorted(raw_pdfs_path.iterdir()):
                if year_folder.is_dir():
                    year = year_folder.name
                    year_folder_id = self.create_folder(year, raw_pdfs_folder_id)

                    if year_folder_id:
                        # Create session folders
                        for session_folder in sorted(year_folder.iterdir()):
                            if session_folder.is_dir():
                                session = session_folder.name
                                session_folder_id = self.create_folder(session, year_folder_id)

                                if session_folder_id:
                                    # Upload PDFs
                                    for pdf_file in sorted(session_folder.glob('*.pdf')):
                                        if self.upload_file(pdf_file, session_folder_id):
                                            uploaded_count += 1

        logger.info("\n" + "="*60)
        logger.info(f"Upload complete: {uploaded_count} files uploaded")
        logger.info("="*60 + "\n")


if __name__ == "__main__":
    """
    To use this uploader:

    1. Set up Google Cloud Project:
       - Go to https://console.cloud.google.com/
       - Create a new project or select existing
       - Enable Google Drive API
       - Create OAuth 2.0 credentials (Desktop app)
       - Download credentials as 'credentials.json'

    2. Run authentication:
       uploader = DriveUploader()
       uploader.authenticate()

    3. Upload dataset:
       uploader.upload_dataset()
    """

    uploader = DriveUploader()

    print("Google Drive Uploader")
    print("=" * 60)
    print("\nTo use this uploader, you need to:")
    print("1. Set up OAuth2 credentials from Google Cloud Console")
    print("2. Download credentials.json to this directory")
    print("3. Run the authentication flow")
    print("\nSee docstring for detailed instructions.")
    print("=" * 60)
