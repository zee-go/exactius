"""
Credential resolution for ClickUp → Meta sync.

Maps an incoming ClickUp task to the correct Meta ad account credentials,
supporting both single-account (local .env) and multi-account (Secret Manager)
modes.

Account selection (multi-account):
    Each ClickUp task carries a custom dropdown field (default name
    "Meta Ad Account", configurable via CLICKUP_ACCOUNT_FIELD). The editor
    picks the target account per task; the option label is the Meta account
    identifier — a short name ("nike") or ad account ID ("act_123456789") —
    which is resolved through AccountManager.

    If no account is selected, NoAccountSelectedError is raised so the caller
    can skip the task and log a warning (nothing is uploaded to a wrong account).
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.config import Config
from src.clickup.parser import extract_selected_account

logger = logging.getLogger(__name__)


class NoAccountSelectedError(Exception):
    """Raised when a task has no Meta ad account selected in its custom field."""


@dataclass
class MetaCredentials:
    """Everything needed to initialise the Meta API and upload for one account."""

    ad_account_id: str
    access_token: str
    app_id: str
    app_secret: str


def resolve_clickup_token(config: Config, secret_manager: Optional[Any] = None) -> str:
    """
    Resolve the ClickUp API token.

    Prefers the CLICKUP_API_TOKEN env var (single-account / local dev); falls
    back to the shared Secret Manager secret in multi-account mode.

    Raises:
        ValueError: If no token can be found.
    """
    if config.clickup_api_token:
        return config.clickup_api_token

    if secret_manager is not None:
        token = secret_manager.get_clickup_token()
        if token:
            return token

    raise ValueError(
        "ClickUp API token not configured. Set CLICKUP_API_TOKEN, or store secret "
        "'exactius-shared-clickup-api-token' in Secret Manager for multi-account mode."
    )


def resolve_meta_credentials(
    task: Dict[str, Any],
    config: Config,
    account_manager: Optional[Any] = None,
) -> MetaCredentials:
    """
    Resolve Meta credentials for the account selected on a ClickUp task.

    In multi-account mode the account is read from the task's "Meta Ad Account"
    custom field. In single-account mode the local .env account is used and the
    field is ignored (there is only one account).

    Args:
        task: Task dict from ClickUpClient.get_task() (must include custom_fields
            for multi-account resolution).
        config: Application config (determines mode).
        account_manager: AccountManager instance (required in multi-account mode).

    Returns:
        MetaCredentials for the resolved account.

    Raises:
        NoAccountSelectedError: If the task has no account chosen (multi-account).
        ValueError: If the selected account can't be loaded or config is missing.
    """
    # Multi-account mode takes precedence when a GCP project is configured.
    if config.is_multi_account_mode():
        if account_manager is None:
            raise ValueError("account_manager is required in multi-account mode")

        identifier = extract_selected_account(task, config.clickup_account_field)
        if not identifier:
            raise NoAccountSelectedError(
                f"Task {task.get('id')} has no '{config.clickup_account_field}' "
                f"selected — skipping."
            )

        try:
            account_data = account_manager.get_account(identifier)
        except Exception as e:
            raise ValueError(
                f"Selected account '{identifier}' could not be loaded: {e}"
            )

        shared = account_data["shared"]
        return MetaCredentials(
            ad_account_id=account_data["account_id"],
            access_token=account_data["token"],
            app_id=shared["app_id"],
            app_secret=shared["app_secret"],
        )

    # Single-account mode: everything comes from the local config/.env.
    if not (config.ad_account_id and config.access_token):
        raise ValueError(
            "Single-account Meta credentials not configured "
            "(FB_AD_ACCOUNT_ID / FB_ACCESS_TOKEN)."
        )
    return MetaCredentials(
        ad_account_id=config.ad_account_id,
        access_token=config.access_token,
        app_id=config.app_id or "",
        app_secret=config.app_secret or "",
    )
