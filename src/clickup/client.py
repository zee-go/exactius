"""
ClickUp API client for asset retrieval.

Authenticates using a personal API token and downloads video attachments
from tasks for upload to Meta Ad Library.
"""

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


@dataclass
class ClickUpAttachment:
    """Represents a ClickUp task attachment."""

    attachment_id: str
    name: str
    url: str
    mime_type: str
    size: int
    task_id: str
    task_name: str
    local_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attachment_id": self.attachment_id,
            "name": self.name,
            "url": self.url,
            "mime_type": self.mime_type,
            "size": self.size,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "local_path": str(self.local_path) if self.local_path else None,
        }


class ClickUpClient:
    """ClickUp REST API client using personal API token."""

    def __init__(self, api_token: str):
        """
        Args:
            api_token: ClickUp personal API token (starts with pk_)
        """
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({"Authorization": api_token})
        logger.info("Initialized ClickUpClient")

    def get_tasks_in_list(self, list_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all tasks in a ClickUp list.

        Args:
            list_id: ClickUp list ID

        Returns:
            List of task dicts

        Raises:
            ValueError: On API error
        """
        tasks = []
        page = 0

        while True:
            resp = self.session.get(
                f"{CLICKUP_API_BASE}/list/{list_id}/task",
                params={"page": page, "include_attachments": True},
            )
            self._raise_for_status(resp)
            data = resp.json()
            batch = data.get("tasks", [])
            tasks.extend(batch)

            # ClickUp paginates in pages of 100; stop when we get a short page
            if len(batch) < 100:
                break
            page += 1

        logger.info(f"Fetched {len(tasks)} task(s) from list {list_id}")
        return tasks

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Fetch a single task with its attachments.

        Args:
            task_id: ClickUp task ID

        Returns:
            Task dict

        Raises:
            ValueError: On API error
        """
        resp = self.session.get(
            f"{CLICKUP_API_BASE}/task/{task_id}",
            params={"include_attachments": True},
        )
        self._raise_for_status(resp)
        return resp.json()

    def download_attachment(
        self,
        attachment: ClickUpAttachment,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Download an attachment file to disk.

        The attachment URL is a pre-signed S3 URL — no extra auth needed
        beyond having obtained it from the API.

        Args:
            attachment: ClickUpAttachment to download
            output_dir: Directory to save file (defaults to system temp)

        Returns:
            Path to downloaded file

        Raises:
            ValueError: If download fails
        """
        if output_dir is None:
            output_dir = Path(tempfile.gettempdir()) / "exactius-assets"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitise filename to avoid path traversal
        safe_name = Path(attachment.name).name or attachment.attachment_id
        dest = output_dir / safe_name

        logger.info(f"Downloading attachment: {attachment.name} ({attachment.size} bytes)")

        try:
            with self.session.get(attachment.url, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        fh.write(chunk)
        except requests.RequestException as e:
            raise ValueError(f"Failed to download attachment {attachment.name}: {e}")

        logger.info(f"Downloaded to: {dest}")
        return dest

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _raise_for_status(self, resp: requests.Response) -> None:
        if resp.status_code == 401:
            raise ValueError("ClickUp authentication failed — check CLICKUP_API_TOKEN")
        if resp.status_code == 404:
            raise ValueError(f"ClickUp resource not found: {resp.url}")
        if not resp.ok:
            raise ValueError(
                f"ClickUp API error {resp.status_code}: {resp.text[:200]}"
            )
