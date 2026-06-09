"""
ClickUp → Meta Ad Library sync workflow.

Downloads video attachments from a ClickUp task and uploads them to Meta
AdVideos (media library) for use in ad creatives.
"""

import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from src.clickup.client import ClickUpClient, ClickUpAttachment
from src.clickup.parser import extract_video_attachments
from src.campaigns.creative_manager import CreativeManager
from src.config import get_config

logger = logging.getLogger(__name__)


def sync_task_videos_to_meta(
    task_id: str,
    ad_account_id: str,
    access_token: str,
) -> List[Dict[str, Any]]:
    """
    Download all video attachments from a ClickUp task and upload to Meta.

    Args:
        task_id: ClickUp task ID
        ad_account_id: Meta ad account ID (format: act_123456789)
        access_token: Meta access token for the ad account

    Returns:
        List of dicts: [{"name": str, "meta_video_id": str, "task_id": str}]

    Raises:
        ValueError: If ClickUp token is not configured or upload fails
    """
    config = get_config()

    if not config.clickup_api_token:
        raise ValueError("CLICKUP_API_TOKEN is not configured")

    clickup = ClickUpClient(config.clickup_api_token)
    creative_mgr = CreativeManager(ad_account_id, access_token)

    # Fetch task and extract video attachments
    task = clickup.get_task(task_id)
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
            # Download from ClickUp
            local_path = clickup.download_attachment(attachment, output_dir=output_dir)

            # Upload to Meta
            meta_video_id = creative_mgr.upload_video(local_path)

            results.append({
                "name": attachment.name,
                "meta_video_id": meta_video_id,
                "task_id": task_id,
                "task_name": attachment.task_name,
            })

            logger.info(
                f"Synced '{attachment.name}' → Meta video ID {meta_video_id}"
            )

        except Exception as e:
            logger.error(f"Failed to sync attachment '{attachment.name}': {e}")
            # Continue with remaining attachments rather than aborting
        finally:
            # Clean up temp file
            if local_path and local_path.exists():
                local_path.unlink(missing_ok=True)

    logger.info(
        f"Sync complete: {len(results)}/{len(attachments)} video(s) uploaded to Meta"
    )
    return results
