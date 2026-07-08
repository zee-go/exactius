"""Tests for ClickUp → Meta credential resolution."""

import pytest

from src.clickup.resolver import (
    MetaCredentials,
    NoAccountSelectedError,
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
        self.clickup_account_field = kw.get("clickup_account_field", "Meta Ad Account")

    def is_multi_account_mode(self):
        return self._multi


class FakeSecretManager:
    def __init__(self, token=None):
        self._token = token

    def get_clickup_token(self):
        return self._token


class FakeAccountManager:
    def __init__(self, secret_manager, accounts):
        self.secret_manager = secret_manager
        self._accounts = accounts

    def get_account(self, identifier):
        return self._accounts[identifier]


def _task_with_account(option_name, *, value=0):
    """Build a task whose 'Meta Ad Account' dropdown selects `option_name`."""
    return {
        "id": "t1",
        "custom_fields": [
            {
                "name": "Meta Ad Account",
                "type": "drop_down",
                "value": value,
                "type_config": {
                    "options": [
                        {"id": "opt-0", "name": option_name, "orderindex": 0},
                        {"id": "opt-1", "name": "other", "orderindex": 1},
                    ]
                },
            }
        ],
    }


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
# Meta credential resolution — single account
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


# ------------------------------------------------------------------
# Meta credential resolution — multi account (custom field)
# ------------------------------------------------------------------

def _account_manager():
    return FakeAccountManager(
        FakeSecretManager(),
        accounts={
            "nike": {
                "account_id": "act_999",
                "token": "tok999",
                "shared": {"app_id": "sid", "app_secret": "ssec"},
            }
        },
    )


def test_multi_account_reads_custom_field_by_orderindex():
    cfg = FakeConfig(multi=True)
    creds = resolve_meta_credentials(_task_with_account("nike", value=0), cfg, _account_manager())
    assert creds == MetaCredentials("act_999", "tok999", "sid", "ssec")


def test_multi_account_reads_custom_field_by_option_id():
    cfg = FakeConfig(multi=True)
    creds = resolve_meta_credentials(_task_with_account("nike", value="opt-0"), cfg, _account_manager())
    assert creds == MetaCredentials("act_999", "tok999", "sid", "ssec")


def test_multi_account_no_selection_raises_no_account():
    cfg = FakeConfig(multi=True)
    task = {"id": "t1", "custom_fields": [
        {"name": "Meta Ad Account", "type": "drop_down", "value": None,
         "type_config": {"options": []}}
    ]}
    with pytest.raises(NoAccountSelectedError):
        resolve_meta_credentials(task, cfg, _account_manager())


def test_multi_account_missing_field_raises_no_account():
    cfg = FakeConfig(multi=True)
    with pytest.raises(NoAccountSelectedError):
        resolve_meta_credentials({"id": "t1", "custom_fields": []}, cfg, _account_manager())


def test_multi_account_unknown_account_raises_value_error():
    cfg = FakeConfig(multi=True)
    task = _task_with_account("ghost", value=0)  # option label not in account manager
    with pytest.raises(ValueError, match="could not be loaded"):
        resolve_meta_credentials(task, cfg, _account_manager())


def test_multi_account_requires_account_manager():
    cfg = FakeConfig(multi=True)
    with pytest.raises(ValueError, match="account_manager is required"):
        resolve_meta_credentials(_task_with_account("nike"), cfg, None)
