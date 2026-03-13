"""
Campaign management functionality
Create, update, and manage Facebook ad campaigns
"""

import logging
from typing import Dict, List, Optional

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign

from src.utils.retry import with_retry

logger = logging.getLogger(__name__)


class CampaignManager:
    """Manages Facebook ad campaigns."""

    def __init__(self, ad_account: AdAccount):
        """
        Initialize campaign manager.

        Args:
            ad_account: AdAccount instance
        """
        self.ad_account = ad_account

    @with_retry()
    def get_campaigns(
        self,
        fields: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Campaign]:
        """
        Fetch campaigns from ad account.

        Args:
            fields: List of fields to retrieve
            limit: Maximum number of campaigns to fetch

        Returns:
            List of Campaign objects
        """
        if fields is None:
            fields = [
                'name',
                'status',
                'objective',
                'daily_budget',
                'lifetime_budget',
                'start_time',
                'stop_time'
            ]

        campaigns = self.ad_account.get_campaigns(
            fields=fields,
            params={'limit': limit}
        )

        return list(campaigns)

    @with_retry()
    def create_campaign(
        self,
        name: str,
        objective: str,
        status: str = 'PAUSED',
        **kwargs
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            objective: Campaign objective (e.g., 'CONVERSIONS', 'TRAFFIC')
            status: Initial status ('ACTIVE' or 'PAUSED')
            **kwargs: Additional campaign parameters

        Returns:
            Created Campaign object
        """
        params = {
            Campaign.Field.name: name,
            Campaign.Field.objective: objective,
            Campaign.Field.status: status,
            **kwargs
        }

        logger.info(f"Creating campaign: {name} (objective: {objective})")

        campaign = self.ad_account.create_campaign(params=params)
        logger.info(f"Campaign created with ID: {campaign['id']}")

        return campaign

    @with_retry()
    def update_campaign(
        self,
        campaign_id: str,
        updates: Dict
    ) -> bool:
        """
        Update an existing campaign.

        Args:
            campaign_id: Campaign ID
            updates: Dictionary of fields to update

        Returns:
            True if update successful
        """
        campaign = Campaign(campaign_id)

        logger.info(f"Updating campaign {campaign_id}: {updates}")

        campaign.api_update(params=updates)
        logger.info(f"Campaign {campaign_id} updated successfully")

        return True

    def pause_campaign(self, campaign_id: str) -> bool:
        """
        Pause a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if paused successfully
        """
        return self.update_campaign(
            campaign_id,
            {Campaign.Field.status: 'PAUSED'}
        )

    def activate_campaign(self, campaign_id: str) -> bool:
        """
        Activate a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if activated successfully
        """
        return self.update_campaign(
            campaign_id,
            {Campaign.Field.status: 'ACTIVE'}
        )

    def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If deletion fails
        """
        try:
            logger.info(f"Deleting campaign: {campaign_id}")

            campaign = Campaign(campaign_id)
            campaign.remote_delete()

            logger.info(f"Campaign deleted: {campaign_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete campaign {campaign_id}: {str(e)}")
            raise ValueError(f"Campaign deletion failed: {str(e)}")

    def get_campaign(self, campaign_id: str) -> Dict:
        """
        Get campaign details.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign data dictionary

        Raises:
            ValueError: If fetch fails
        """
        try:
            campaign = Campaign(campaign_id)
            campaign_data = campaign.api_get(fields=[
                Campaign.Field.id,
                Campaign.Field.name,
                Campaign.Field.status,
                Campaign.Field.objective,
                Campaign.Field.daily_budget,
                Campaign.Field.lifetime_budget,
            ])

            return dict(campaign_data)

        except Exception as e:
            logger.error(f"Failed to fetch campaign {campaign_id}: {str(e)}")
            raise ValueError(f"Campaign fetch failed: {str(e)}")
