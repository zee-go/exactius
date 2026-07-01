"""Tests for ClickUp attachment parsing."""

from src.clickup.parser import extract_video_attachments


def test_extracts_video_by_mimetype():
    task = {
        "id": "abc123",
        "name": "Q3 Creative",
        "attachments": [
            {
                "id": "att1",
                "title": "hero.mp4",
                "mimetype": "video/mp4",
                "url": "https://s3.example.com/hero.mp4?sig=x",
                "size": 1024,
            }
        ],
    }
    videos = extract_video_attachments(task)
    assert len(videos) == 1
    assert videos[0].name == "hero.mp4"
    assert videos[0].task_id == "abc123"
    assert videos[0].task_name == "Q3 Creative"


def test_extracts_video_by_extension_when_mime_missing():
    task = {
        "id": "t1",
        "name": "task",
        "attachments": [
            {
                "id": "att1",
                "title": "clip.mov",
                "mimetype": "",
                "url": "https://s3.example.com/clip.mov?sig=x",
                "size": 2048,
            }
        ],
    }
    videos = extract_video_attachments(task)
    assert len(videos) == 1
    assert videos[0].mime_type == "video/mp4"  # default fallback


def test_ignores_images_and_docs():
    task = {
        "id": "t1",
        "name": "task",
        "attachments": [
            {"id": "a", "title": "photo.png", "mimetype": "image/png", "url": "https://x/p.png"},
            {"id": "b", "title": "brief.pdf", "mimetype": "application/pdf", "url": "https://x/b.pdf"},
        ],
    }
    assert extract_video_attachments(task) == []


def test_skips_attachment_without_url():
    task = {
        "id": "t1",
        "name": "task",
        "attachments": [
            {"id": "a", "title": "broken.mp4", "mimetype": "video/mp4", "url": ""},
        ],
    }
    assert extract_video_attachments(task) == []


def test_empty_task_returns_empty():
    assert extract_video_attachments({}) == []
