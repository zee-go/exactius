"""
FastAPI dependencies for dependency injection.

Provides reusable dependencies for Secret Manager, Account Manager,
and other shared resources.
"""

import os
import logging
from functools import lru_cache
from typing import Optional

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from src.secrets.manager import SecretManagerClient
from src.accounts.manager import AccountManager

logger = logging.getLogger(__name__)

# API key header scheme
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: Optional[str] = Security(_api_key_header)) -> None:
    """
    Validate the X-API-Key header against the API_KEY environment variable.

    If API_KEY is not set, authentication is skipped (development mode).
    Set API_KEY in production to enforce access control.
    """
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        # Dev mode: no key configured, allow all requests
        return

    if not api_key or api_key != expected_key:
        logger.warning("Rejected request with invalid or missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )


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
