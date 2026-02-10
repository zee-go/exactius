"""
Pydantic models for campaign-related API endpoints.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class CampaignType(BaseModel):
    """Campaign type information."""

    name: str = Field(..., description="Campaign type name")
    display_name: Optional[str] = Field(None, description="Human-readable name")


class CampaignLaunchRequest(BaseModel):
    """Request body for launching a new campaign."""

    account_id: str = Field(..., description="Meta ad account ID")
    campaign_type: str = Field(..., description="Campaign type (e.g., traffic_campaign)")
    drive_url: str = Field(..., description="Google Drive folder/file URL")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Template variables for naming (product, audience, etc.)"
    )
    preview_only: bool = Field(
        default=False,
        description="If true, return preview without creating campaigns"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "act_123456789",
                "campaign_type": "traffic_campaign",
                "drive_url": "https://drive.google.com/drive/folders/ABC123",
                "context": {
                    "product": "AirMax",
                    "audience_type": "Broad"
                },
                "preview_only": False
            }
        }
