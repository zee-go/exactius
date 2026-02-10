"""
Account management for multi-tenant agency operations.

Handles account listing, selection, and credential loading for multiple
client ad accounts stored in Google Secret Manager.
"""

import logging
from typing import Dict, Any, List, Optional

from src.secrets.manager import SecretManagerClient

logger = logging.getLogger(__name__)


class AccountManager:
    """Manages multiple Meta ad accounts for agency use."""

    def __init__(self, secret_manager: SecretManagerClient):
        """
        Initialize account manager.

        Args:
            secret_manager: SecretManagerClient instance for credential access
        """
        self.secret_manager = secret_manager
        logger.info("Initialized AccountManager")

    def list_accounts(self) -> List[Dict[str, str]]:
        """
        List all available ad accounts.

        Returns:
            List of account dictionaries:
                - id: Meta ad account ID (e.g., "act_123456789")
                - name: Short name (e.g., "nike")
                - display_name: Human-readable name (e.g., "Nike - US Market")

        Raises:
            ValueError: If no accounts found
        """
        return self.secret_manager.list_accounts()

    def get_account(self, account_identifier: str) -> Dict[str, Any]:
        """
        Get account by ID or name.

        Args:
            account_identifier: Either account ID (act_123456789) or name (nike)

        Returns:
            Account info dictionary with keys:
                - id: Account ID
                - name: Short name
                - display_name: Full name
                - config: Full account configuration
                - credentials: Meta access token and shared credentials

        Raises:
            ValueError: If account not found
        """
        accounts = self.list_accounts()

        # Try to find by ID first, then by name
        account = None
        for acc in accounts:
            if acc['id'] == account_identifier or acc['name'] == account_identifier:
                account = acc
                break

        if not account:
            available = ', '.join([f"{a['name']} ({a['id']})" for a in accounts])
            raise ValueError(
                f"Account '{account_identifier}' not found. "
                f"Available accounts: {available}"
            )

        # Load full account data
        return self.load_account_credentials(account['id'])

    def load_account_credentials(self, account_id: str) -> Dict[str, Any]:
        """
        Load full account configuration and credentials.

        Args:
            account_id: Meta ad account ID

        Returns:
            Dictionary containing:
                - account_id: Meta ad account ID
                - config: Full account configuration (naming rules, defaults, etc.)
                - token: Meta access token for this account
                - shared: Shared credentials (app ID/secret, Drive service account)

        Raises:
            ValueError: If account not found or credentials invalid
        """
        try:
            logger.info(f"Loading credentials for account: {account_id}")

            # Fetch account-specific data
            config = self.secret_manager.get_account_config(account_id)
            token = self.secret_manager.get_account_token(account_id)

            # Fetch shared credentials
            shared = self.secret_manager.get_shared_credentials()

            account_data = {
                'account_id': account_id,
                'config': config,
                'token': token,
                'shared': shared
            }

            logger.info(f"Successfully loaded credentials for {config['display_name']}")
            return account_data

        except Exception as e:
            logger.error(f"Failed to load credentials for {account_id}: {str(e)}")
            raise

    def validate_account_access(self, account_id: str) -> bool:
        """
        Validate that account credentials are accessible and valid.

        Args:
            account_id: Meta ad account ID

        Returns:
            True if account access is valid, False otherwise
        """
        try:
            account_data = self.load_account_credentials(account_id)

            # Basic validation: check that we have required fields
            required_fields = ['config', 'token', 'shared']
            for field in required_fields:
                if field not in account_data or not account_data[field]:
                    logger.error(f"Missing or empty field '{field}' for account {account_id}")
                    return False

            # Validate config structure
            config = account_data['config']
            required_config_fields = ['account_id', 'account_name', 'display_name', 'naming_rules']
            for field in required_config_fields:
                if field not in config:
                    logger.error(f"Missing config field '{field}' for account {account_id}")
                    return False

            # Validate shared credentials structure
            shared = account_data['shared']
            required_shared = ['app_id', 'app_secret', 'drive_service_account']
            for field in required_shared:
                if field not in shared or not shared[field]:
                    logger.error(f"Missing shared credential '{field}'")
                    return False

            logger.info(f"Account {account_id} validation passed")
            return True

        except Exception as e:
            logger.error(f"Account validation failed for {account_id}: {str(e)}")
            return False

    def get_campaign_types(self, account_id: str) -> List[str]:
        """
        Get available campaign types for an account.

        Args:
            account_id: Meta ad account ID

        Returns:
            List of campaign type names (keys from naming_rules)
        """
        config = self.secret_manager.get_account_config(account_id)
        naming_rules = config.get('naming_rules', {})
        return list(naming_rules.keys())
