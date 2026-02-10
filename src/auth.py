"""
Facebook API authentication and initialization
"""

import logging
from typing import Optional

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

from config import Config

logger = logging.getLogger(__name__)


class FacebookAuth:
    """Handles Facebook Marketing API authentication and initialization."""

    def __init__(self, config: Config):
        """
        Initialize Facebook API authentication.

        Args:
            config: Configuration object with API credentials
        """
        self.config = config
        self._api_instance: Optional[FacebookAdsApi] = None

    def get_api_instance(self) -> FacebookAdsApi:
        """
        Get or create Facebook API instance.

        Returns:
            Initialized FacebookAdsApi instance
        """
        if self._api_instance is None:
            logger.info(f"Initializing Facebook API {self.config.api_version}")

            FacebookAdsApi.init(
                app_id=self.config.app_id,
                app_secret=self.config.app_secret,
                access_token=self.config.access_token,
                api_version=self.config.api_version
            )

            self._api_instance = FacebookAdsApi.get_default_api()
            logger.info("Facebook API initialized successfully")

        return self._api_instance

    def get_ad_account(self) -> AdAccount:
        """
        Get AdAccount object for the configured ad account.

        Returns:
            AdAccount instance
        """
        # Ensure API is initialized
        self.get_api_instance()

        return AdAccount(self.config.ad_account_id)

    def validate_access(self) -> bool:
        """
        Validate API access by attempting to fetch ad account info.

        Returns:
            True if access is valid, False otherwise
        """
        try:
            account = self.get_ad_account()
            account.api_get(fields=['name'])
            return True
        except Exception as e:
            logger.error(f"Access validation failed: {str(e)}")
            return False
