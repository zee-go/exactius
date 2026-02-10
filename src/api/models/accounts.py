"""
Pydantic models for account-related API endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AccountInfo(BaseModel):
    """Basic account information for listing."""

    id: str = Field(..., description="Meta ad account ID (e.g., act_123456789)")
    name: str = Field(..., description="Short account name (e.g., nike)")
    display_name: str = Field(..., description="Human-readable account name")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "act_123456789",
                "name": "nike",
                "display_name": "Nike - US Market"
            }
        }


class AccountListResponse(BaseModel):
    """Response for list accounts endpoint."""

    accounts: List[AccountInfo] = Field(..., description="List of available accounts")
    count: int = Field(..., description="Total number of accounts")

    class Config:
        json_schema_extra = {
            "example": {
                "accounts": [
                    {
                        "id": "act_123456789",
                        "name": "nike",
                        "display_name": "Nike - US Market"
                    }
                ],
                "count": 1
            }
        }


class NamingRule(BaseModel):
    """Naming rule template for a campaign entity."""

    campaign: str = Field(..., description="Campaign name template")
    adset: str = Field(..., description="Ad set name template")
    ad: str = Field(..., description="Ad name template")


class AccountDetail(BaseModel):
    """Detailed account information including configuration."""

    account_id: str = Field(..., description="Meta ad account ID")
    account_name: str = Field(..., description="Short account name")
    display_name: str = Field(..., description="Human-readable account name")
    campaign_types: List[str] = Field(..., description="Available campaign types")
    naming_rules: Dict[str, Any] = Field(..., description="Naming rules per campaign type")
    defaults: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default values for templates"
    )
    meta: Optional[Dict[str, str]] = Field(
        default=None,
        description="Meta-specific IDs (business_id, page_id)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "act_123456789",
                "account_name": "nike",
                "display_name": "Nike - US Market",
                "campaign_types": ["traffic_campaign", "conversions_campaign"],
                "naming_rules": {
                    "traffic_campaign": {
                        "campaign": "{client}_{product}_Traffic_{date}",
                        "adset": "{client}_{product}_{audience_type}_{date}",
                        "ad": "{client}_{product}_{creative_type}_{variant}"
                    }
                },
                "defaults": {
                    "client": "Nike",
                    "geo_locations": ["US"],
                    "currency": "USD"
                },
                "meta": {
                    "business_id": "123456789",
                    "page_id": "987654321"
                }
            }
        }
