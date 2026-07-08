"""
Credential resolution for ClickUp → Meta sync.

Maps an incoming ClickUp task to the correct Meta ad account credentials,
supporting both single-account (local .env) and multi-account (Secret Manager)
modes.

Multi-account mapping:
    A shared Secret Manager secret `exactius-shared-clickup-account-map`
    holds a JSON object mapping ClickUp list IDs to Meta account identifiers
    (either an account ID "act_123" or a short name "nike"), e.g.:

        {
          "901100011": "nike",
          "901100022": "act_123456789"
        }

    When a webhook fires, the task's list ID is looked up here to decide
    which account's videos it belongs to.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.config import Config

logger = logging.getLogger(__name__)


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
    Resolve Meta credentials for the account a ClickUp task belongs to.

    Args:
        task: Task dict from ClickUpClient.get_task() (must include `list.id`
            for multi-account resolution).
        config: Application config (determines mode).
        account_manager: AccountManager instance (required in multi-account mode).

    Returns:
        MetaCredentials for the resolved account.

    Raises:
        ValueError: If the account can't be resolved or credentials are missing.
    """
    # Multi-account mode takes precedence when a GCP project is configured.
    if config.is_multi_account_mode():
        if account_manager is None:
            raise ValueError("account_manager is required in multi-account mode")

        list_id = str((task.get("list") or {}).get("id") or "")
        if not list_id:
            raise ValueError(
                f"Task {task.get('id')} has no list ID — cannot map to an account"
            )

        account_map = account_manager.secret_manager.get_clickup_account_map()
        identifier = account_map.get(list_id)
        if not identifier:
            raise ValueError(
                f"No account mapping for ClickUp list '{list_id}'. Add it to the "
                f"'exactius-shared-clickup-account-map' secret."
            )

        account_data = account_manager.get_account(identifier)
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
