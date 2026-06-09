"""ClickUp integration for asset retrieval."""

from src.clickup.client import ClickUpClient, ClickUpAttachment
from src.clickup.parser import extract_video_attachments

__all__ = ['ClickUpClient', 'ClickUpAttachment', 'extract_video_attachments']
