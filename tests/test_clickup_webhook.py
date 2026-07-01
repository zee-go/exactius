"""Tests for the ClickUp webhook endpoint (signature + status filtering)."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

import src.api.routes.clickup as clickup_route
import src.config as config_module
from src.api.main import app
from src.config import get_config

client = TestClient(app, raise_server_exceptions=False)

SECRET = "test-secret"


@pytest.fixture(autouse=True)
def configure(monkeypatch):
    """Force a known config for each test."""
    # Ensure config validates in a clean test env (multi-account mode only
    # needs GOOGLE_CLOUD_PROJECT). Rebuild the singleton so it picks this up.
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setattr(config_module, "_config_instance", None)
    cfg = get_config()
    monkeypatch.setattr(cfg, "clickup_webhook_secret", SECRET)
    monkeypatch.setattr(cfg, "clickup_trigger_status", "ready for ads")
    monkeypatch.setattr(cfg, "ad_account_id", "act_123")
    monkeypatch.setattr(cfg, "access_token", "token")
    yield


def _sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def _payload(new_status: str) -> dict:
    return {
        "event": "taskStatusUpdated",
        "task_id": "task123",
        "history_items": [
            {"field": "status", "after": {"status": new_status}},
        ],
    }


def test_rejects_missing_signature():
    resp = client.post("/api/clickup/webhook", json=_payload("ready for ads"))
    assert resp.status_code == 401


def test_rejects_bad_signature():
    body = json.dumps(_payload("ready for ads")).encode()
    resp = client.post(
        "/api/clickup/webhook",
        content=body,
        headers={"X-Signature": "wrong"},
    )
    assert resp.status_code == 401


def test_triggers_sync_on_matching_status(monkeypatch):
    called = {}

    def fake_sync(task_id, ad_account_id, access_token):
        called["task_id"] = task_id
        return [{"name": "v.mp4", "meta_video_id": "999"}]

    monkeypatch.setattr(clickup_route, "sync_task_videos_to_meta", fake_sync)

    body = json.dumps(_payload("ready for ads")).encode()
    resp = client.post(
        "/api/clickup/webhook",
        content=body,
        headers={"X-Signature": _sign(body)},
    )
    assert resp.status_code == 200
    assert resp.json().get("sync") == "queued"
    # BackgroundTasks run after response in TestClient
    assert called.get("task_id") == "task123"


def test_ignores_non_trigger_status(monkeypatch):
    called = {}
    monkeypatch.setattr(
        clickup_route,
        "sync_task_videos_to_meta",
        lambda *a, **k: called.setdefault("ran", True),
    )
    body = json.dumps(_payload("in progress")).encode()
    resp = client.post(
        "/api/clickup/webhook",
        content=body,
        headers={"X-Signature": _sign(body)},
    )
    assert resp.status_code == 200
    assert "sync" not in resp.json()
    assert "ran" not in called


def test_ignores_non_status_events():
    body = json.dumps({"event": "taskUpdated"}).encode()
    resp = client.post(
        "/api/clickup/webhook",
        content=body,
        headers={"X-Signature": _sign(body)},
    )
    assert resp.status_code == 200
    assert resp.json() == {"received": True}
