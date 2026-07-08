"""
ClickUp webhook and manual sync routes.

Handles incoming ClickUp webhooks (taskStatusUpdated) and triggers the
ClickUp → Meta video sync when a task reaches the configured trigger status
(default: "ready for ads"). Works in both single-account (.env) and
multi-account (Secret Manager) modes.
"""

import hashlib
import hmac
import json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel

from src.config import get_config
from src.clickup.resolver import MetaCredentials
from src.orchestrator.clickup_sync import sync_task_auto, sync_task_videos_to_meta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clickup", tags=["clickup"])


# ------------------------------------------------------------------
# Request / response models
# ------------------------------------------------------------------

class ManualSyncRequest(BaseModel):
    task_id: str
    ad_account_id: str
    access_token: str
    app_id: Optional[str] = None
    app_secret: Optional[str] = None


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

    ClickUp sends taskStatusUpdated events signed with HMAC-SHA256. When a task
    reaches the configured trigger status, its video attachments are downloaded
    and uploaded to Meta AdVideos in the background (fast 200 back to ClickUp).

    Register this endpoint via scripts/register_clickup_webhook.py.
    """
    config = get_config()
    raw_body = await request.body()

    # Verify signature if a webhook secret is configured.
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
        # Acknowledge non-actionable events immediately.
        return {"received": True}

    # Find the status-change entry (don't assume it's the first history item).
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

    logger.info(f"Task {task_id} reached '{new_status}' — queuing video sync")

    # Build an account manager only in multi-account mode (needs a GCP project).
    account_manager = None
    if config.is_multi_account_mode():
        from src.api.dependencies import get_account_manager
        account_manager = get_account_manager()

    background_tasks.add_task(_run_sync, task_id=task_id, account_manager=account_manager)

    return {"received": True, "task_id": task_id, "sync": "queued"}


# ------------------------------------------------------------------
# Manual sync endpoint (fallback / testing)
# ------------------------------------------------------------------

@router.post("/sync-videos", response_model=SyncResult)
async def manual_sync_videos(body: ManualSyncRequest):
    """
    Manually trigger video sync for a specific ClickUp task with explicit
    Meta credentials. Useful for testing or one-off syncs.

    app_id / app_secret fall back to the local config if omitted.
    """
    config = get_config()
    creds = MetaCredentials(
        ad_account_id=body.ad_account_id,
        access_token=body.access_token,
        app_id=body.app_id or config.app_id or "",
        app_secret=body.app_secret or config.app_secret or "",
    )

    results = sync_task_videos_to_meta(body.task_id, creds)

    return SyncResult(
        task_id=body.task_id,
        videos_uploaded=len(results),
        results=results,
    )


# ------------------------------------------------------------------
# Internal helper
# ------------------------------------------------------------------

def _run_sync(task_id: str, account_manager=None) -> None:
    """Background task wrapper with top-level error catching."""
    try:
        results = sync_task_auto(task_id, account_manager=account_manager)
        logger.info(
            f"Background sync finished for task {task_id}: "
            f"{len(results)} video(s) uploaded"
        )
    except Exception as e:
        logger.error(f"Background sync failed for task {task_id}: {e}", exc_info=True)
