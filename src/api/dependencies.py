"""
FastAPI dependencies for dependency injection.

Provides reusable dependencies for Secret Manager, Account Manager,
and other shared resources.
"""

import os
import logging
from functools import lru_cache
from typing import Optional

from src.secrets.manager import SecretManagerClient
from src.accounts.manager import AccountManager

logger = logging.getLogger(__name__)


@lru_cache()
def get_google_cloud_project_id() -> str:
    """
    Get Google Cloud project ID from environment.

    Returns:
        Project ID string

    Raises:
        ValueError: If GOOGLE_CLOUD_PROJECT not set
    """
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT environment variable not set. "
            "Please set it to your Google Cloud project ID."
        )
    return project_id


@lru_cache()
def get_secret_manager() -> SecretManagerClient:
    """
    Get Secret Manager client singleton.

    Returns:
        SecretManagerClient instance
    """
    project_id = get_google_cloud_project_id()
    logger.info(f"Initializing Secret Manager for project: {project_id}")
    return SecretManagerClient(project_id)


def get_account_manager() -> AccountManager:
    """
    Get Account Manager instance.

    Returns:
        AccountManager instance with Secret Manager dependency
    """
    secret_manager = get_secret_manager()
    return AccountManager(secret_manager)
