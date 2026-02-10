"""
Google Drive API client for asset retrieval.

Authenticates using service account credentials from Secret Manager
and downloads files from shared Drive folders.
"""

import io
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class DriveAsset:
    """Represents a Drive asset with metadata."""

    def __init__(
        self,
        file_id: str,
        name: str,
        mime_type: str,
        size: int,
        local_path: Optional[Path] = None
    ):
        """
        Initialize Drive asset.

        Args:
            file_id: Google Drive file ID
            name: File name
            mime_type: MIME type
            size: File size in bytes
            local_path: Local path after download
        """
        self.file_id = file_id
        self.name = name
        self.mime_type = mime_type
        self.size = size
        self.local_path = local_path

    def __repr__(self) -> str:
        return f"DriveAsset(name={self.name}, type={self.mime_type}, size={self.size})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_id': self.file_id,
            'name': self.name,
            'mime_type': self.mime_type,
            'size': self.size,
            'local_path': str(self.local_path) if self.local_path else None
        }


class DriveClient:
    """Google Drive API client with service account authentication."""

    # Supported image/video MIME types for Meta ads
    SUPPORTED_IMAGE_TYPES = [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
    ]

    SUPPORTED_VIDEO_TYPES = [
        'video/mp4',
        'video/quicktime',  # .mov
        'video/avi',
        'video/x-msvideo',
    ]

    def __init__(self, service_account_json: str):
        """
        Initialize Drive client with service account.

        Args:
            service_account_json: Service account credentials JSON string
        """
        self.credentials = self._load_credentials(service_account_json)
        self.service = build('drive', 'v3', credentials=self.credentials)
        logger.info("Initialized Drive client with service account")

    def _load_credentials(self, credentials_json: str) -> service_account.Credentials:
        """
        Load service account credentials from JSON string.

        Args:
            credentials_json: Service account JSON as string

        Returns:
            Service account credentials
        """
        try:
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            return credentials
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid service account JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load service account credentials: {str(e)}")

    def list_folder_files(
        self,
        folder_id: str,
        filter_supported: bool = True
    ) -> List[DriveAsset]:
        """
        List files in a Drive folder.

        Args:
            folder_id: Google Drive folder ID
            filter_supported: If True, only return supported image/video types

        Returns:
            List of DriveAsset objects

        Raises:
            ValueError: If folder not found or access denied
        """
        try:
            logger.info(f"Listing files in folder: {folder_id}")

            # Query for files in folder
            query = f"'{folder_id}' in parents and trashed=false"

            # Add MIME type filter if requested
            if filter_supported:
                supported_types = self.SUPPORTED_IMAGE_TYPES + self.SUPPORTED_VIDEO_TYPES
                type_query = ' or '.join([f"mimeType='{t}'" for t in supported_types])
                query += f" and ({type_query})"

            results = self.service.files().list(
                q=query,
                fields='files(id, name, mimeType, size)',
                pageSize=1000,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])

            assets = [
                DriveAsset(
                    file_id=f['id'],
                    name=f['name'],
                    mime_type=f['mimeType'],
                    size=int(f.get('size', 0))
                )
                for f in files
            ]

            logger.info(f"Found {len(assets)} file(s) in folder")
            return assets

        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Folder not found: {folder_id}")
            elif e.resp.status == 403:
                raise ValueError(
                    f"Access denied to folder: {folder_id}. "
                    f"Make sure the folder is shared with the service account."
                )
            else:
                raise ValueError(f"Drive API error: {str(e)}")

    def download_file(
        self,
        file_id: str,
        output_dir: Optional[Path] = None,
        filename: Optional[str] = None
    ) -> Path:
        """
        Download a file from Drive.

        Args:
            file_id: Google Drive file ID
            output_dir: Directory to save file (default: temp directory)
            filename: Output filename (default: original filename)

        Returns:
            Path to downloaded file

        Raises:
            ValueError: If file not found or download fails
        """
        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name, mimeType',
                supportsAllDrives=True
            ).execute()

            file_name = filename or file_metadata['name']

            # Prepare output path
            if output_dir is None:
                output_dir = Path(tempfile.gettempdir()) / 'exactius-assets'
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / file_name

            logger.info(f"Downloading file: {file_name}")

            # Download file
            request = self.service.files().get_media(
                fileId=file_id,
                supportsAllDrives=True
            )

            with io.FileIO(output_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.debug(f"Download progress: {progress}%")

            logger.info(f"Downloaded: {output_path}")
            return output_path

        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"File not found: {file_id}")
            elif e.resp.status == 403:
                raise ValueError(
                    f"Access denied to file: {file_id}. "
                    f"Make sure the file is shared with the service account."
                )
            else:
                raise ValueError(f"Drive API error: {str(e)}")

    def download_folder(
        self,
        folder_id: str,
        output_dir: Optional[Path] = None,
        filter_supported: bool = True
    ) -> List[DriveAsset]:
        """
        Download all files from a Drive folder.

        Args:
            folder_id: Google Drive folder ID
            output_dir: Directory to save files (default: temp directory)
            filter_supported: If True, only download supported image/video types

        Returns:
            List of DriveAsset objects with local_path set

        Raises:
            ValueError: If folder not found or access denied
        """
        logger.info(f"Downloading folder: {folder_id}")

        # List files
        assets = self.list_folder_files(folder_id, filter_supported)

        if not assets:
            logger.warning(f"No files found in folder: {folder_id}")
            return []

        # Download each file
        downloaded_assets = []
        for asset in assets:
            try:
                local_path = self.download_file(
                    asset.file_id,
                    output_dir=output_dir,
                    filename=asset.name
                )
                asset.local_path = local_path
                downloaded_assets.append(asset)
            except Exception as e:
                logger.error(f"Failed to download {asset.name}: {str(e)}")
                continue

        logger.info(f"Downloaded {len(downloaded_assets)}/{len(assets)} files")
        return downloaded_assets

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get file metadata.

        Args:
            file_id: Google Drive file ID

        Returns:
            File metadata dictionary

        Raises:
            ValueError: If file not found
        """
        try:
            metadata = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime',
                supportsAllDrives=True
            ).execute()

            return metadata

        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"File not found: {file_id}")
            else:
                raise ValueError(f"Drive API error: {str(e)}")

    def is_supported_type(self, mime_type: str) -> bool:
        """
        Check if MIME type is supported for Meta ads.

        Args:
            mime_type: MIME type string

        Returns:
            True if supported, False otherwise
        """
        return mime_type in (self.SUPPORTED_IMAGE_TYPES + self.SUPPORTED_VIDEO_TYPES)

    def is_image(self, mime_type: str) -> bool:
        """Check if MIME type is an image."""
        return mime_type in self.SUPPORTED_IMAGE_TYPES

    def is_video(self, mime_type: str) -> bool:
        """Check if MIME type is a video."""
        return mime_type in self.SUPPORTED_VIDEO_TYPES
