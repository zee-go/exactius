"""
ClickUp attachment parsing utilities.

Filters task attachments to video files supported by Meta Ad Library.
"""

from typing import List, Dict, Any, Optional

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


def extract_selected_account(task: Dict[str, Any], field_name: str) -> Optional[str]:
    """
    Read the Meta ad account chosen on a ClickUp task's custom field.

    Looks for a custom field named `field_name` (case-insensitive). For a
    drop_down field, resolves the selected value (which ClickUp may return as an
    option orderindex, option id, or option name) to that option's label. For a
    text field, returns the raw string.

    The returned value is the account identifier (Meta account short name like
    "nike" or ad account ID like "act_123456789") — i.e. whatever the dropdown
    option is labelled.

    Args:
        task: Task dict from ClickUpClient.get_task().
        field_name: Name of the custom field to read (e.g. "Meta Ad Account").

    Returns:
        The selected account identifier, or None if the field is absent/empty.
    """
    target = field_name.strip().lower()

    for field in task.get("custom_fields", []) or []:
        if (field.get("name") or "").strip().lower() != target:
            continue

        value = field.get("value")
        if value is None or value == "":
            return None

        if field.get("type") == "drop_down":
            options = (field.get("type_config") or {}).get("options", []) or []
            # ClickUp may return the selection as orderindex (int) or option id (str).
            for opt in options:
                if value == opt.get("orderindex") or str(value) == str(opt.get("id")):
                    return opt.get("name")
            # Or the value may already be the option name.
            for opt in options:
                if str(value).strip().lower() == (opt.get("name") or "").strip().lower():
                    return opt.get("name")
            return None

        # Text-style fields: use the raw value if it's a usable string.
        if isinstance(value, str):
            return value.strip() or None
        return None

    return None


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
