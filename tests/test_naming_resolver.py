"""
Tests for NamingResolver.
"""

import pytest
from src.naming.resolver import NamingResolver


def make_account_config(campaign_templates=None, defaults=None):
    """Build a minimal account config dict.

    NamingResolver uses Python string.Template ($variable syntax).
    """
    return {
        "account_id": "act_123456789",
        "account_name": "testclient",
        "display_name": "Test Client",
        "naming_rules": {
            "traffic_campaign": campaign_templates or {
                "campaign": "${client}_${product}_Traffic_${date}",
                "adset": "${client}_${product}_${audience_type}_AS",
                "ad": "${client}_${product}_${audience_type}_Ad",
            }
        },
        "defaults": defaults or {
            "client": "TestClient",
        },
    }


CONTEXT = {"product": "AirMax", "audience_type": "Broad"}


class TestInit:

    def test_valid_campaign_type_initializes(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        assert resolver.campaign_type == "traffic_campaign"

    def test_invalid_campaign_type_raises(self):
        config = make_account_config()
        with pytest.raises(ValueError, match="not found in naming rules"):
            NamingResolver(config, "unknown_type")


class TestGenerateName:

    def test_template_substitution(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        name = resolver.generate_name("campaign", CONTEXT)
        assert "AirMax" in name
        assert "Traffic" in name
        assert "TestClient" in name  # from defaults

    def test_date_auto_injected(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        name = resolver.generate_name("campaign", CONTEXT)
        # Date should be in YYYY-MM-DD format
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", name)

    def test_account_name_auto_injected(self):
        config = make_account_config(
            campaign_templates={
                "campaign": "${account_name}_Campaign",
                "adset": "${account_name}_AdSet",
                "ad": "${account_name}_Ad",
            }
        )
        resolver = NamingResolver(config, "traffic_campaign")
        name = resolver.generate_name("campaign", {})
        assert "testclient" in name

    def test_context_overrides_defaults(self):
        config = make_account_config(defaults={"client": "DefaultClient"})
        resolver = NamingResolver(config, "traffic_campaign")
        name = resolver.generate_name("campaign", {**CONTEXT, "client": "OverrideClient"})
        assert "OverrideClient" in name
        assert "DefaultClient" not in name

    def test_unknown_entity_type_raises(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        with pytest.raises(ValueError, match="No naming rule"):
            resolver.generate_name("unknown_entity", CONTEXT)


class TestPreviewNames:

    def test_returns_all_three_keys(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        names = resolver.preview_names(CONTEXT)
        assert set(names.keys()) == {"campaign", "adset", "ad"}

    def test_all_values_are_strings(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        names = resolver.preview_names(CONTEXT)
        for name in names.values():
            assert isinstance(name, str)

    def test_missing_variable_still_returns_dict(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        # Missing audience_type — should not raise, just return partial/error name
        names = resolver.preview_names({"product": "AirMax"})
        assert "campaign" in names


class TestValidateContext:

    def test_valid_context_returns_true(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        is_valid, missing = resolver.validate_context(CONTEXT)
        assert is_valid is True
        assert missing == []

    def test_missing_variable_returns_false(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        is_valid, missing = resolver.validate_context({"product": "AirMax"})
        # audience_type is required but missing
        assert is_valid is False
        assert any("audience_type" in m for m in missing)

    def test_defaults_satisfy_requirements(self):
        # If all variables have defaults, empty context is valid
        config = make_account_config(
            campaign_templates={
                "campaign": "${client}_Campaign_${date}",
                "adset": "${client}_AdSet",
                "ad": "${client}_Ad",
            },
            defaults={"client": "DefaultClient"},
        )
        resolver = NamingResolver(config, "traffic_campaign")
        is_valid, missing = resolver.validate_context({})
        assert is_valid is True


class TestGetRequiredVariables:

    def test_extracts_template_vars(self):
        config = make_account_config()
        resolver = NamingResolver(config, "traffic_campaign")
        required = resolver.get_required_variables("campaign")
        # {client} is in defaults, {date} is auto-var — so only {product} is required
        assert "product" in required
        assert "date" not in required  # auto-var
        assert "client" not in required  # in defaults

    def test_custom_function_returns_empty(self):
        config = make_account_config(
            campaign_templates={
                "campaign": "custom.my_namer",
                "adset": "{product}_AdSet",
                "ad": "{product}_Ad",
            }
        )
        resolver = NamingResolver(config, "traffic_campaign")
        required = resolver.get_required_variables("campaign")
        assert required == []
