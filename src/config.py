"""
Configuration management for Exactius

Supports two modes:
1. Production: Uses Google Secret Manager for all credentials
2. Development: Uses local .env file for testing (legacy single-account mode)

The application automatically detects which mode to use based on environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """
    Application configuration.

    For multi-account production use, only GOOGLE_CLOUD_PROJECT is required.
    All other credentials are fetched from Secret Manager.

    For local development/testing, can still use .env file with single account.
    """

    # Google Cloud configuration
    google_cloud_project: Optional[str] = None

    # Legacy single-account fields (for local development)
    access_token: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    ad_account_id: Optional[str] = None

    # API settings
    api_version: str = 'v19.0'
    log_level: str = 'INFO'

    # Google Sheets settings
    spreadsheet_id: Optional[str] = None
    sheet_name: str = 'Sheet1'
    oauth_client_secrets_path: Optional[str] = None

    # Asset processing settings
    temp_download_dir: str = '/tmp/exactius-assets'
    max_image_size_mb: int = 30
    max_video_size_mb: int = 4096

    def __init__(self):
        """Load configuration from environment variables."""
        # Load .env file if it exists (for local development)
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        # Google Cloud project (required for production multi-account mode)
        self.google_cloud_project = os.getenv('GOOGLE_CLOUD_PROJECT')

        # Legacy single-account variables (optional, for local development)
        self.access_token = os.getenv('FB_ACCESS_TOKEN')
        self.app_id = os.getenv('FB_APP_ID')
        self.app_secret = os.getenv('FB_APP_SECRET')
        self.ad_account_id = os.getenv('FB_AD_ACCOUNT_ID')

        # API settings
        self.api_version = os.getenv('FB_API_VERSION', 'v19.0')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

        # Google Sheets settings
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID', '1zZz1azGTfrWtuInoB39jiJBy9PDNGr7Ogr5GMCfsVmA')
        self.sheet_name = os.getenv('SHEET_NAME', 'Sheet1')
        self.oauth_client_secrets_path = os.getenv(
            'GOOGLE_OAUTH_CLIENT_SECRETS',
            str(Path.home() / '.exactius' / 'client_secret.json')
        )

        # Asset processing settings
        self.temp_download_dir = os.getenv('TEMP_DOWNLOAD_DIR', '/tmp/exactius-assets')
        self.max_image_size_mb = int(os.getenv('MAX_IMAGE_SIZE_MB', '30'))
        self.max_video_size_mb = int(os.getenv('MAX_VIDEO_SIZE_MB', '4096'))

        # Validate ad account ID format if provided
        if self.ad_account_id and not self.ad_account_id.startswith('act_'):
            raise ValueError(
                f"Invalid ad account ID format: {self.ad_account_id}. "
                "Must start with 'act_'"
            )

    def is_multi_account_mode(self) -> bool:
        """
        Check if running in multi-account mode (Secret Manager).

        Returns:
            True if GOOGLE_CLOUD_PROJECT is set (production mode)
        """
        return self.google_cloud_project is not None

    def is_single_account_mode(self) -> bool:
        """
        Check if running in single-account mode (local .env).

        Returns:
            True if all legacy credentials are set
        """
        return all([
            self.access_token,
            self.app_id,
            self.app_secret,
            self.ad_account_id
        ])

    def validate(self) -> None:
        """
        Validate configuration based on mode.

        Raises:
            ValueError: If required variables are missing for the detected mode
        """
        if self.is_multi_account_mode():
            # Multi-account mode: only need project ID
            # All other credentials fetched from Secret Manager
            return

        if self.is_single_account_mode():
            # Single-account mode: all legacy credentials present
            return

        # Neither mode fully configured
        raise ValueError(
            "Configuration incomplete. Either:\n"
            "1. Set GOOGLE_CLOUD_PROJECT for multi-account mode (production), OR\n"
            "2. Set FB_ACCESS_TOKEN, FB_APP_ID, FB_APP_SECRET, FB_AD_ACCOUNT_ID "
            "for single-account mode (local development)\n\n"
            "For production deployment, use Google Secret Manager with GOOGLE_CLOUD_PROJECT."
        )

    def __repr__(self) -> str:
        """String representation with masked sensitive data."""
        if self.is_multi_account_mode():
            return (
                f"Config(mode=multi-account, "
                f"project={self.google_cloud_project}, "
                f"api_version={self.api_version})"
            )
        elif self.is_single_account_mode():
            return (
                f"Config(mode=single-account, "
                f"app_id={self.app_id}, "
                f"ad_account_id={self.ad_account_id}, "
                f"api_version={self.api_version}, "
                f"access_token={'*' * 20}...)"
            )
        else:
            return "Config(mode=unconfigured)"


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create singleton Config instance.

    Returns:
        Config instance

    Raises:
        ValueError: If configuration is invalid
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        _config_instance.validate()
    return _config_instance
