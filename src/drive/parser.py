"""
Google Drive URL parser.

Supports multiple Drive URL formats:
- https://drive.google.com/drive/folders/{FOLDER_ID}
- https://drive.google.com/file/d/{FILE_ID}/view
- https://drive.google.com/open?id={FILE_ID}
- https://drive.google.com/drive/u/0/folders/{FOLDER_ID}
"""

import re
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class DriveURLParser:
    """Parse Google Drive URLs and extract file/folder IDs."""

    # Regex patterns for different Drive URL formats
    FOLDER_PATTERN = r'/folders/([a-zA-Z0-9_-]+)'
    FILE_PATTERN = r'/file/d/([a-zA-Z0-9_-]+)'
    OPEN_PATTERN = r'/open\?id=([a-zA-Z0-9_-]+)'

    @staticmethod
    def parse(url: str) -> Tuple[str, str]:
        """
        Parse Drive URL and extract resource type and ID.

        Args:
            url: Google Drive URL

        Returns:
            Tuple of (resource_type, resource_id)
            - resource_type: 'folder' or 'file'
            - resource_id: Drive resource ID

        Raises:
            ValueError: If URL format is invalid or not a Drive URL
        """
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")

        # Clean up URL
        url = url.strip()

        # Validate it's a Google Drive URL
        parsed = urlparse(url)
        if 'drive.google.com' not in parsed.netloc:
            raise ValueError(
                f"Invalid Google Drive URL. Domain must be 'drive.google.com', got: {parsed.netloc}"
            )

        # Try folder pattern
        folder_match = re.search(DriveURLParser.FOLDER_PATTERN, url)
        if folder_match:
            folder_id = folder_match.group(1)
            logger.debug(f"Parsed folder ID: {folder_id}")
            return ('folder', folder_id)

        # Try file pattern
        file_match = re.search(DriveURLParser.FILE_PATTERN, url)
        if file_match:
            file_id = file_match.group(1)
            logger.debug(f"Parsed file ID: {file_id}")
            return ('file', file_id)

        # Try open pattern (legacy)
        open_match = re.search(DriveURLParser.OPEN_PATTERN, url)
        if open_match:
            resource_id = open_match.group(1)
            logger.debug(f"Parsed resource ID (open): {resource_id}")
            # Can't determine type from open URL, default to folder
            return ('folder', resource_id)

        # Try query parameter
        query_params = parse_qs(parsed.query)
        if 'id' in query_params:
            resource_id = query_params['id'][0]
            logger.debug(f"Parsed resource ID (query): {resource_id}")
            return ('folder', resource_id)

        raise ValueError(
            f"Could not extract file or folder ID from URL: {url}\n"
            "Supported formats:\n"
            "  - https://drive.google.com/drive/folders/FOLDER_ID\n"
            "  - https://drive.google.com/file/d/FILE_ID/view\n"
            "  - https://drive.google.com/open?id=RESOURCE_ID"
        )

    @staticmethod
    def extract_id(url: str) -> str:
        """
        Extract resource ID from Drive URL (type-agnostic).

        Args:
            url: Google Drive URL

        Returns:
            Resource ID string

        Raises:
            ValueError: If URL format is invalid
        """
        _, resource_id = DriveURLParser.parse(url)
        return resource_id

    @staticmethod
    def extract_folder_id(url: str) -> str:
        """
        Extract folder ID from Drive URL.

        Args:
            url: Google Drive folder URL

        Returns:
            Folder ID string

        Raises:
            ValueError: If URL is not a folder or invalid
        """
        resource_type, resource_id = DriveURLParser.parse(url)
        if resource_type != 'folder':
            raise ValueError(f"URL is not a folder: {url}")
        return resource_id

    @staticmethod
    def extract_file_id(url: str) -> str:
        """
        Extract file ID from Drive URL.

        Args:
            url: Google Drive file URL

        Returns:
            File ID string

        Raises:
            ValueError: If URL is not a file or invalid
        """
        resource_type, resource_id = DriveURLParser.parse(url)
        if resource_type != 'file':
            raise ValueError(f"URL is not a file: {url}")
        return resource_id

    @staticmethod
    def is_valid_drive_url(url: str) -> bool:
        """
        Check if URL is a valid Google Drive URL.

        Args:
            url: URL to validate

        Returns:
            True if valid Drive URL, False otherwise
        """
        try:
            DriveURLParser.parse(url)
            return True
        except (ValueError, AttributeError, TypeError):
            return False
