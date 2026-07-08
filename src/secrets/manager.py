"""
Google Secret Manager client for managing credentials and account configurations.

This module handles:
- Fetching Meta access tokens per account
- Loading account configurations (naming rules, defaults)
- Managing shared credentials (Meta app ID/secret, Drive service account)
- Listing available accounts
"""

import json
import logging
from typing import Dict, Any, List, Optional

from google.cloud import secretmanager
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)


class SecretManagerClient:
    """Manages secrets in Google Secret Manager."""

    def __init__(self, project_id: str):
        """
        Initialize Secret Manager client.

        Args:
            project_id: Google Cloud project ID
        """
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
        logger.info(f"Initialized Secret Manager client for project: {project_id}")

    def get_account_token(self, account_id: str) -> str:
        """
        Fetch Meta access token for specific account.

        Args:
            account_id: Meta ad account ID (e.g., "act_123456789")

        Returns:
            Meta access token string

        Raises:
            ValueError: If secret not found or invalid account ID
        """
        # Convert account_id format: act_123456789 -> exactius-accounts-act_123456789-meta-access-token
        secret_id = f"exactius-accounts-{account_id}-meta-access-token"
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"

        try:
            logger.debug(f"Fetching access token for account: {account_id}")
            response = self.client.access_secret_version(request={"name": secret_name})
            token = response.payload.data.decode('UTF-8')
            logger.info(f"Successfully retrieved access token for {account_id}")
            return token
        except google_exceptions.NotFound:
            raise ValueError(
                f"Access token not found for account '{account_id}'. "
                f"Expected secret: {secret_id}"
            )
        except Exception as e:
            logger.error(f"Failed to fetch access token for {account_id}: {str(e)}")
            raise

    def get_account_config(self, account_id: str) -> Dict[str, Any]:
        """
        Fetch account configuration including naming rules and defaults.

        Args:
            account_id: Meta ad account ID (e.g., "act_123456789")

        Returns:
            Dictionary containing account configuration:
                - account_id: Meta ad account ID
                - account_name: Short name (e.g., "nike")
                - display_name: Human-readable name
                - meta: Meta-specific IDs (business_id, page_id)
                - naming_rules: Per-campaign-type naming templates
                - defaults: Default values for templates

        Raises:
            ValueError: If secret not found or invalid JSON
        """
        secret_id = f"exactius-accounts-{account_id}-config"
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"

        try:
            logger.debug(f"Fetching config for account: {account_id}")
            response = self.client.access_secret_version(request={"name": secret_name})
            config_json = response.payload.data.decode('UTF-8')
            config = json.loads(config_json)

            # Validate required fields
            required_fields = ['account_id', 'account_name', 'display_name', 'naming_rules']
            missing_fields = [f for f in required_fields if f not in config]
            if missing_fields:
                raise ValueError(
                    f"Invalid config for {account_id}: missing fields {missing_fields}"
                )

            logger.info(f"Successfully retrieved config for {account_id}")
            return config

        except google_exceptions.NotFound:
            raise ValueError(
                f"Configuration not found for account '{account_id}'. "
                f"Expected secret: {secret_id}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config for {account_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to fetch config for {account_id}: {str(e)}")
            raise

    def get_shared_credentials(self) -> Dict[str, str]:
        """
        Fetch shared Meta app credentials and Drive service account.

        Returns:
            Dictionary containing:
                - app_id: Meta app ID
                - app_secret: Meta app secret
                - drive_service_account: Google Drive service account JSON

        Raises:
            ValueError: If any shared secret not found
        """
        try:
            logger.debug("Fetching shared credentials")

            credentials = {
                'app_id': self._get_secret('exactius-shared-meta-app-id'),
                'app_secret': self._get_secret('exactius-shared-meta-app-secret'),
                'drive_service_account': self._get_secret('exactius-shared-google-drive-service-account')
            }

            logger.info("Successfully retrieved shared credentials")
            return credentials

        except Exception as e:
            logger.error(f"Failed to fetch shared credentials: {str(e)}")
            raise

    def list_accounts(self) -> List[Dict[str, str]]:
        """
        List all configured accounts by finding config secrets.

        Returns:
            List of account dictionaries with keys:
                - id: Meta ad account ID
                - name: Short name
                - display_name: Human-readable name

        Raises:
            ValueError: If no accounts found
        """
        try:
            logger.debug("Listing all accounts")
            parent = f"projects/{self.project_id}"

            # List all secrets
            request = secretmanager.ListSecretsRequest(parent=parent)
            secrets = self.client.list_secrets(request=request)

            accounts = []
            for secret in secrets:
                secret_id = secret.name.split('/')[-1]

                # Look for config secrets: exactius-accounts-{account_id}-config
                if secret_id.startswith('exactius-accounts-') and secret_id.endswith('-config'):
                    # Extract account_id from secret name
                    # Format: exactius-accounts-act_123456789-config
                    account_id = secret_id.replace('exactius-accounts-', '').replace('-config', '')

                    try:
                        config = self.get_account_config(account_id)
                        accounts.append({
                            'id': config['account_id'],
                            'name': config['account_name'],
                            'display_name': config['display_name']
                        })
                    except Exception as e:
                        logger.warning(f"Skipping invalid account config {account_id}: {str(e)}")
                        continue

            if not accounts:
                raise ValueError(
                    "No accounts configured in Secret Manager. "
                    "Please create account configurations following the setup guide."
                )

            logger.info(f"Found {len(accounts)} configured accounts")
            return sorted(accounts, key=lambda x: x['name'])

        except Exception as e:
            logger.error(f"Failed to list accounts: {str(e)}")
            raise

    def get_clickup_token(self) -> Optional[str]:
        """
        Fetch the shared ClickUp API token, if configured.

        Returns:
            ClickUp personal API token, or None if the secret is not set.
        """
        try:
            return self._get_secret('exactius-shared-clickup-api-token')
        except ValueError:
            logger.debug("Shared ClickUp API token secret not configured")
            return None

    def _get_secret(self, secret_id: str) -> str:
        """
        Internal helper to fetch a secret value.

        Args:
            secret_id: Secret identifier (without project path)

        Returns:
            Secret value as string

        Raises:
            ValueError: If secret not found
        """
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"

        try:
            response = self.client.access_secret_version(request={"name": secret_name})
            return response.payload.data.decode('UTF-8')
        except google_exceptions.NotFound:
            raise ValueError(f"Secret '{secret_id}' not found in project {self.project_id}")
        except Exception as e:
            raise ValueError(f"Failed to access secret '{secret_id}': {str(e)}")

    def _extract_account_id(self, secret_name: str) -> str:
        """
        Extract account ID from secret name.

        Args:
            secret_name: Full secret name from API

        Returns:
            Account ID (e.g., "act_123456789")
        """
        # Example: projects/PROJECT/secrets/exactius-accounts-act_123456789-config
        parts = secret_name.split('/')
        secret_id = parts[-1]  # exactius-accounts-act_123456789-config

        # Remove prefix and suffix
        account_id = secret_id.replace('exactius-accounts-', '').replace('-config', '')
        return account_id
