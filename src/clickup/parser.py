"""
ClickUp attachment parsing utilities.

Filters task attachments to video files supported by Meta Ad Library.
"""

from typing import List, Dict, Any

from src.clickup.client import ClickUpAttachment

SUPPORTED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",   # .mov
    "video/avi",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/webm",
}

# Fallback: treat these extensions as video if MIME type is missing/generic
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".wmv", ".webm", ".m4v"}


def extract_video_attachments(task: Dict[str, Any]) -> List[ClickUpAttachment]:
    """
    Extract video attachments from a ClickUp task dict.

    Args:
        task: Task dict returned by ClickUpClient.get_task()

    Returns:
        List of ClickUpAttachment objects for video files only
    """
    task_id = task.get("id", "")
    task_name = task.get("name", "")
    raw_attachments = task.get("attachments", [])

    results = []
    for att in raw_attachments:
        name = att.get("title") or att.get("name") or ""
        mime = (att.get("mimetype") or att.get("content_type") or "").lower()
        url = att.get("url") or att.get("url_w_query") or ""
        size = int(att.get("size") or 0)
        att_id = att.get("id") or att.get("attachment_id") or ""

        if not url:
            continue

        ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
        is_video = mime in SUPPORTED_VIDEO_MIME_TYPES or ext in SUPPORTED_VIDEO_EXTENSIONS

        if is_video:
            results.append(
                ClickUpAttachment(
                    attachment_id=att_id,
                    name=name,
                    url=url,
                    mime_type=mime or "video/mp4",
                    size=size,
                    task_id=task_id,
                    task_name=task_name,
                )
            )

    return results
