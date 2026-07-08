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
    """Force a known single-account config for each test (no GCP needed)."""
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setenv("FB_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("FB_APP_ID", "aid")
    monkeypatch.setenv("FB_APP_SECRET", "asec")
    monkeypatch.setenv("FB_AD_ACCOUNT_ID", "act_123")
    monkeypatch.setattr(config_module, "_config_instance", None)

    cfg = get_config()
    monkeypatch.setattr(cfg, "clickup_webhook_secret", SECRET)
    monkeypatch.setattr(cfg, "clickup_trigger_status", "ready for ads")
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

    def fake_sync(task_id, account_manager=None):
        called["task_id"] = task_id
        return [{"name": "v.mp4", "meta_video_id": "999"}]

    monkeypatch.setattr(clickup_route, "sync_task_auto", fake_sync)

    body = json.dumps(_payload("ready for ads")).encode()
    resp = client.post(
        "/api/clickup/webhook",
        content=body,
        headers={"X-Signature": _sign(body)},
    )
    assert resp.status_code == 200
    assert resp.json().get("sync") == "queued"
    # BackgroundTasks run after the response in TestClient.
    assert called.get("task_id") == "task123"


def test_ignores_non_trigger_status(monkeypatch):
    called = {}
    monkeypatch.setattr(
        clickup_route,
        "sync_task_auto",
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
