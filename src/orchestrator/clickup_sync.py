"""
ClickUp → Meta Ad Library sync workflow.

Downloads video attachments from a ClickUp task and uploads them to Meta
AdVideos (media library) for use in ad creatives.

Two entry points:
- sync_task_videos_to_meta(): low-level worker, explicit credentials.
- sync_task_auto():           resolves credentials (single- or multi-account)
                              from the task itself, then runs the worker.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from facebook_business.api import FacebookAdsApi

from src.clickup.client import ClickUpClient
from src.clickup.parser import extract_video_attachments
from src.clickup.resolver import (
    MetaCredentials,
    resolve_clickup_token,
    resolve_meta_credentials,
)
from src.campaigns.creative_manager import CreativeManager
from src.config import get_config

logger = logging.getLogger(__name__)


def sync_task_videos_to_meta(
    task_id: str,
    creds: MetaCredentials,
    *,
    clickup_client: Optional[ClickUpClient] = None,
    task: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Download all video attachments from a ClickUp task and upload to Meta.

    Args:
        task_id: ClickUp task ID.
        creds: Resolved Meta credentials for the target ad account.
        clickup_client: Optional pre-built ClickUp client (avoids re-auth).
        task: Optional pre-fetched task dict (avoids a duplicate API call).

    Returns:
        List of dicts: [{"name", "meta_video_id", "task_id", "task_name"}]
    """
    config = get_config()

    # Initialise the Meta API session for this account. CreativeManager relies
    # on the module-level FacebookAdsApi default session being set (it does not
    # init the API itself — see CampaignLauncher).
    FacebookAdsApi.init(
        app_id=creds.app_id,
        app_secret=creds.app_secret,
        access_token=creds.access_token,
    )

    if clickup_client is None:
        clickup_client = ClickUpClient(resolve_clickup_token(config))
    if task is None:
        task = clickup_client.get_task(task_id)

    creative_mgr = CreativeManager(creds.ad_account_id, creds.access_token)

    attachments = extract_video_attachments(task)
    if not attachments:
        logger.info(f"No video attachments found on task {task_id}")
        return []

    logger.info(f"Found {len(attachments)} video attachment(s) on task {task_id}")

    output_dir = Path(config.temp_download_dir) / "clickup"
    results = []

    for attachment in attachments:
        local_path = None
        try:
            local_path = clickup_client.download_attachment(attachment, output_dir=output_dir)
            meta_video_id = creative_mgr.upload_video(local_path)

            results.append({
                "name": attachment.name,
                "meta_video_id": meta_video_id,
                "task_id": task_id,
                "task_name": attachment.task_name,
            })
            logger.info(f"Synced '{attachment.name}' → Meta video ID {meta_video_id}")

        except Exception as e:
            logger.error(f"Failed to sync attachment '{attachment.name}': {e}")
            # Continue with remaining attachments rather than aborting the batch.
        finally:
            if local_path and local_path.exists():
                local_path.unlink(missing_ok=True)

    logger.info(
        f"Sync complete: {len(results)}/{len(attachments)} video(s) uploaded to Meta"
    )
    return results


def sync_task_auto(
    task_id: str,
    account_manager: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Resolve credentials from the task and sync its videos to Meta.

    This is the entry point used by the webhook: it fetches the task once,
    resolves the correct account (single- or multi-account), and uploads.

    Args:
        task_id: ClickUp task ID.
        account_manager: AccountManager (required in multi-account mode).

    Returns:
        Same shape as sync_task_videos_to_meta().
    """
    config = get_config()

    secret_manager = getattr(account_manager, "secret_manager", None)
    clickup_client = ClickUpClient(resolve_clickup_token(config, secret_manager))

    # Fetch once — we need the list ID (for account mapping) and attachments.
    task = clickup_client.get_task(task_id)

    creds = resolve_meta_credentials(task, config, account_manager)

    return sync_task_videos_to_meta(
        task_id,
        creds,
        clickup_client=clickup_client,
        task=task,
    )
