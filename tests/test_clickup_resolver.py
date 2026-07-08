"""Tests for ClickUp → Meta credential resolution."""

import pytest

from src.clickup.resolver import (
    MetaCredentials,
    resolve_clickup_token,
    resolve_meta_credentials,
)


class FakeConfig:
    """Minimal stand-in for src.config.Config."""

    def __init__(self, multi, **kw):
        self._multi = multi
        self.ad_account_id = kw.get("ad_account_id")
        self.access_token = kw.get("access_token")
        self.app_id = kw.get("app_id")
        self.app_secret = kw.get("app_secret")
        self.clickup_api_token = kw.get("clickup_api_token")

    def is_multi_account_mode(self):
        return self._multi


class FakeSecretManager:
    def __init__(self, token=None, account_map=None):
        self._token = token
        self._map = account_map or {}

    def get_clickup_token(self):
        return self._token

    def get_clickup_account_map(self):
        return self._map


class FakeAccountManager:
    def __init__(self, secret_manager, accounts):
        self.secret_manager = secret_manager
        self._accounts = accounts

    def get_account(self, identifier):
        return self._accounts[identifier]


# ------------------------------------------------------------------
# ClickUp token resolution
# ------------------------------------------------------------------

def test_clickup_token_prefers_env():
    cfg = FakeConfig(multi=False, clickup_api_token="pk_env")
    assert resolve_clickup_token(cfg) == "pk_env"


def test_clickup_token_falls_back_to_secret_manager():
    cfg = FakeConfig(multi=True, clickup_api_token=None)
    sm = FakeSecretManager(token="pk_secret")
    assert resolve_clickup_token(cfg, sm) == "pk_secret"


def test_clickup_token_missing_raises():
    cfg = FakeConfig(multi=True, clickup_api_token=None)
    with pytest.raises(ValueError):
        resolve_clickup_token(cfg, FakeSecretManager(token=None))


# ------------------------------------------------------------------
# Meta credential resolution
# ------------------------------------------------------------------

def test_single_account_uses_config():
    cfg = FakeConfig(
        multi=False,
        ad_account_id="act_123",
        access_token="tok",
        app_id="aid",
        app_secret="asec",
    )
    creds = resolve_meta_credentials({"id": "t1"}, cfg)
    assert creds == MetaCredentials("act_123", "tok", "aid", "asec")


def test_single_account_missing_creds_raises():
    cfg = FakeConfig(multi=False, ad_account_id=None, access_token=None)
    with pytest.raises(ValueError):
        resolve_meta_credentials({"id": "t1"}, cfg)


def test_multi_account_maps_list_to_account():
    cfg = FakeConfig(multi=True)
    sm = FakeSecretManager(account_map={"list1": "nike"})
    am = FakeAccountManager(
        sm,
        accounts={
            "nike": {
                "account_id": "act_999",
                "token": "tok999",
                "shared": {"app_id": "sid", "app_secret": "ssec"},
            }
        },
    )
    task = {"id": "t1", "list": {"id": "list1"}}
    creds = resolve_meta_credentials(task, cfg, am)
    assert creds == MetaCredentials("act_999", "tok999", "sid", "ssec")


def test_multi_account_unmapped_list_raises():
    cfg = FakeConfig(multi=True)
    sm = FakeSecretManager(account_map={"other": "nike"})
    am = FakeAccountManager(sm, accounts={})
    task = {"id": "t1", "list": {"id": "list1"}}
    with pytest.raises(ValueError, match="No account mapping"):
        resolve_meta_credentials(task, cfg, am)


def test_multi_account_requires_account_manager():
    cfg = FakeConfig(multi=True)
    with pytest.raises(ValueError, match="account_manager is required"):
        resolve_meta_credentials({"id": "t1", "list": {"id": "x"}}, cfg, None)
