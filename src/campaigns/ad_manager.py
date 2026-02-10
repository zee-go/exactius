"""
Meta API Ad Manager.

Handles creating and managing ads with creatives.
"""

import logging
from typing import Dict, Any, Optional

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adset import AdSet

logger = logging.getLogger(__name__)


class AdManager:
    """Manages ads in Meta Ads."""

    def __init__(self, ad_account_id: str, access_token: str):
        """
        Initialize ad manager.

        Args:
            ad_account_id: Meta ad account ID (format: act_123456789)
            access_token: Meta access token for this account
        """
        self.ad_account_id = ad_account_id
        self.access_token = access_token
        self.ad_account = AdAccount(ad_account_id)

        logger.info(f"Initialized AdManager for {ad_account_id}")

    def create_ad(
        self,
        adset_id: str,
        creative_id: str,
        ad_name: str,
        status: str = 'PAUSED'
    ) -> str:
        """
        Create an ad.

        Args:
            adset_id: Parent ad set ID
            creative_id: Creative ID to use for this ad
            ad_name: Name for the ad
            status: Ad status (PAUSED or ACTIVE)

        Returns:
            Ad ID

        Raises:
            ValueError: If creation fails
        """
        try:
            logger.info(f"Creating ad: {ad_name}")

            # Build ad params
            ad_params = {
                Ad.Field.name: ad_name,
                Ad.Field.adset_id: adset_id,
                Ad.Field.creative: {'creative_id': creative_id},
                Ad.Field.status: status,
            }

            # Create ad
            ad = Ad(parent_id=self.ad_account_id)
            ad.update(ad_params)
            ad.remote_create()

            ad_id = ad[Ad.Field.id]
            logger.info(f"Ad created. ID: {ad_id}, Status: {status}")

            return ad_id

        except Exception as e:
            logger.error(f"Failed to create ad '{ad_name}': {str(e)}")
            raise ValueError(f"Ad creation failed: {str(e)}")

    def update_ad(
        self,
        ad_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing ad.

        Args:
            ad_id: Ad ID to update
            updates: Dictionary of fields to update

        Returns:
            True if update successful

        Raises:
            ValueError: If update fails
        """
        try:
            logger.info(f"Updating ad: {ad_id}")

            ad = Ad(ad_id)
            ad.update(updates)
            ad.remote_update()

            logger.info(f"Ad updated: {ad_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update ad {ad_id}: {str(e)}")
            raise ValueError(f"Ad update failed: {str(e)}")

    def pause_ad(self, ad_id: str) -> bool:
        """
        Pause an ad.

        Args:
            ad_id: Ad ID to pause

        Returns:
            True if paused successfully
        """
        return self.update_ad(ad_id, {Ad.Field.status: 'PAUSED'})

    def activate_ad(self, ad_id: str) -> bool:
        """
        Activate an ad.

        Args:
            ad_id: Ad ID to activate

        Returns:
            True if activated successfully
        """
        return self.update_ad(ad_id, {Ad.Field.status: 'ACTIVE'})

    def delete_ad(self, ad_id: str) -> bool:
        """
        Delete an ad.

        Args:
            ad_id: Ad ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If deletion fails
        """
        try:
            logger.info(f"Deleting ad: {ad_id}")

            ad = Ad(ad_id)
            ad.remote_delete()

            logger.info(f"Ad deleted: {ad_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete ad {ad_id}: {str(e)}")
            raise ValueError(f"Ad deletion failed: {str(e)}")

    def get_ad(self, ad_id: str) -> Dict[str, Any]:
        """
        Get ad details.

        Args:
            ad_id: Ad ID

        Returns:
            Ad data dictionary

        Raises:
            ValueError: If fetch fails
        """
        try:
            ad = Ad(ad_id)
            ad_data = ad.api_get(fields=[
                Ad.Field.id,
                Ad.Field.name,
                Ad.Field.adset_id,
                Ad.Field.creative,
                Ad.Field.status,
            ])

            return dict(ad_data)

        except Exception as e:
            logger.error(f"Failed to fetch ad {ad_id}: {str(e)}")
            raise ValueError(f"Ad fetch failed: {str(e)}")
