"""
ClickUp webhook and manual sync routes.

Handles incoming ClickUp webhooks (taskStatusUpdated) and triggers
the ClickUp → Meta video sync workflow when a task reaches the
configured trigger status (default: "ready for ads").
"""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional

from src.config import get_config
from src.orchestrator.clickup_sync import sync_task_videos_to_meta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clickup", tags=["clickup"])


# ------------------------------------------------------------------
# Request / response models
# ------------------------------------------------------------------

class ManualSyncRequest(BaseModel):
    task_id: str
    ad_account_id: str
    access_token: str


class SyncResult(BaseModel):
    task_id: str
    videos_uploaded: int
    results: list


# ------------------------------------------------------------------
# Webhook endpoint
# ------------------------------------------------------------------

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def clickup_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
):
    """
    Receive ClickUp webhook events.

    ClickUp sends taskStatusUpdated events signed with HMAC-SHA256.
    When a task reaches the configured trigger status, video attachments
    are downloaded from ClickUp and uploaded to Meta AdVideos in the background.

    Register this endpoint URL in ClickUp via scripts/register_clickup_webhook.py.
    """
    config = get_config()
    raw_body = await request.body()

    # Verify signature if a webhook secret is configured
    if config.clickup_webhook_secret:
        if not x_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Signature header",
            )
        expected = hmac.new(
            config.clickup_webhook_secret.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    try:
        payload = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )

    event = payload.get("event", "")
    if event != "taskStatusUpdated":
        # Acknowledge non-actionable events immediately
        return {"received": True}

    # Find the status-change entry (don't assume it's the first history item)
    history_items = payload.get("history_items", []) or []
    status_item = next(
        (item for item in history_items if item.get("field") == "status"),
        {},
    )

    task_id = payload.get("task_id") or (status_item.get("task", {}) or {}).get("id")
    new_status = (status_item.get("after", {}) or {}).get("status", "").lower()

    if not task_id:
        logger.warning("Webhook payload missing task_id")
        return {"received": True}

    if new_status != config.clickup_trigger_status:
        logger.debug(f"Task {task_id} moved to '{new_status}' — not trigger status, ignoring")
        return {"received": True}

    logger.info(
        f"Task {task_id} reached '{new_status}' — queuing video sync"
    )

    # Resolve account: for now use the default single-account config.
    # In multi-account mode the account mapping should be stored per workspace/list
    # in Secret Manager and looked up here.
    ad_account_id = config.ad_account_id
    access_token = config.access_token

    if not ad_account_id or not access_token:
        logger.error(
            "Cannot sync: FB_AD_ACCOUNT_ID / FB_ACCESS_TOKEN not configured. "
            "Use the manual sync endpoint with explicit credentials."
        )
        return {"received": True, "warning": "Meta credentials not configured for auto-sync"}

    background_tasks.add_task(
        _run_sync,
        task_id=task_id,
        ad_account_id=ad_account_id,
        access_token=access_token,
    )

    return {"received": True, "task_id": task_id, "sync": "queued"}


# ------------------------------------------------------------------
# Manual sync endpoint (fallback / testing)
# ------------------------------------------------------------------

@router.post("/sync-videos", response_model=SyncResult)
async def manual_sync_videos(body: ManualSyncRequest):
    """
    Manually trigger video sync for a specific ClickUp task.

    Useful for testing or one-off syncs without waiting for a webhook.
    """
    results = sync_task_videos_to_meta(
        task_id=body.task_id,
        ad_account_id=body.ad_account_id,
        access_token=body.access_token,
    )

    return SyncResult(
        task_id=body.task_id,
        videos_uploaded=len(results),
        results=results,
    )


# ------------------------------------------------------------------
# Internal helper
# ------------------------------------------------------------------

def _run_sync(task_id: str, ad_account_id: str, access_token: str) -> None:
    """Background task wrapper with top-level error catching."""
    try:
        results = sync_task_videos_to_meta(task_id, ad_account_id, access_token)
        logger.info(
            f"Background sync finished for task {task_id}: "
            f"{len(results)} video(s) uploaded"
        )
    except Exception as e:
        logger.error(f"Background sync failed for task {task_id}: {e}", exc_info=True)
