"""
Meta API AdSet Manager.

Handles creating and managing ad sets with targeting, budget, and optimization settings.
"""

import logging
from typing import Dict, Any, Optional, List

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.targeting import Targeting

logger = logging.getLogger(__name__)


class AdSetManager:
    """Manages ad sets in Meta Ads."""

    def __init__(self, ad_account_id: str, access_token: str):
        """
        Initialize ad set manager.

        Args:
            ad_account_id: Meta ad account ID (format: act_123456789)
            access_token: Meta access token for this account
        """
        self.ad_account_id = ad_account_id
        self.access_token = access_token
        self.ad_account = AdAccount(ad_account_id)

        logger.info(f"Initialized AdSetManager for {ad_account_id}")

    def create_adset(
        self,
        campaign_id: str,
        adset_name: str,
        optimization_goal: str = 'LINK_CLICKS',
        billing_event: str = 'IMPRESSIONS',
        bid_amount: Optional[int] = None,
        daily_budget: Optional[int] = None,
        lifetime_budget: Optional[int] = None,
        targeting: Optional[Dict[str, Any]] = None,
        status: str = 'PAUSED'
    ) -> str:
        """
        Create an ad set.

        Args:
            campaign_id: Parent campaign ID
            adset_name: Name for the ad set
            optimization_goal: Optimization goal (LINK_CLICKS, CONVERSIONS, etc.)
            billing_event: Billing event (IMPRESSIONS, LINK_CLICKS, etc.)
            bid_amount: Bid amount in cents (optional for auto-bidding)
            daily_budget: Daily budget in cents
            lifetime_budget: Lifetime budget in cents
            targeting: Targeting spec (geo, age, gender, interests, etc.)
            status: AdSet status (PAUSED or ACTIVE)

        Returns:
            AdSet ID

        Raises:
            ValueError: If creation fails or invalid parameters
        """
        try:
            logger.info(f"Creating ad set: {adset_name}")

            # Validate budget
            if not daily_budget and not lifetime_budget:
                raise ValueError("Must specify either daily_budget or lifetime_budget")

            if daily_budget and lifetime_budget:
                raise ValueError("Cannot specify both daily_budget and lifetime_budget")

            # Build ad set params
            adset_params = {
                AdSet.Field.name: adset_name,
                AdSet.Field.campaign_id: campaign_id,
                AdSet.Field.optimization_goal: optimization_goal,
                AdSet.Field.billing_event: billing_event,
                AdSet.Field.status: status,
            }

            # Add budget
            if daily_budget:
                adset_params[AdSet.Field.daily_budget] = daily_budget

            if lifetime_budget:
                adset_params[AdSet.Field.lifetime_budget] = lifetime_budget

            # Add bid amount if specified
            if bid_amount:
                adset_params[AdSet.Field.bid_amount] = bid_amount

            # Add targeting
            if targeting:
                adset_params[AdSet.Field.targeting] = targeting
            else:
                # Default targeting: US, ages 18-65
                adset_params[AdSet.Field.targeting] = {
                    Targeting.Field.geo_locations: {
                        'countries': ['US']
                    },
                    Targeting.Field.age_min: 18,
                    Targeting.Field.age_max: 65,
                }

            # Create ad set
            adset = AdSet(parent_id=self.ad_account_id)
            adset.update(adset_params)
            adset.remote_create()

            adset_id = adset[AdSet.Field.id]
            logger.info(f"Ad set created. ID: {adset_id}, Status: {status}")

            return adset_id

        except Exception as e:
            logger.error(f"Failed to create ad set '{adset_name}': {str(e)}")
            raise ValueError(f"AdSet creation failed: {str(e)}")

    def update_adset(
        self,
        adset_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing ad set.

        Args:
            adset_id: AdSet ID to update
            updates: Dictionary of fields to update

        Returns:
            True if update successful

        Raises:
            ValueError: If update fails
        """
        try:
            logger.info(f"Updating ad set: {adset_id}")

            adset = AdSet(adset_id)
            adset.update(updates)
            adset.remote_update()

            logger.info(f"Ad set updated: {adset_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update ad set {adset_id}: {str(e)}")
            raise ValueError(f"AdSet update failed: {str(e)}")

    def pause_adset(self, adset_id: str) -> bool:
        """
        Pause an ad set.

        Args:
            adset_id: AdSet ID to pause

        Returns:
            True if paused successfully
        """
        return self.update_adset(adset_id, {AdSet.Field.status: 'PAUSED'})

    def activate_adset(self, adset_id: str) -> bool:
        """
        Activate an ad set.

        Args:
            adset_id: AdSet ID to activate

        Returns:
            True if activated successfully
        """
        return self.update_adset(adset_id, {AdSet.Field.status: 'ACTIVE'})

    def delete_adset(self, adset_id: str) -> bool:
        """
        Delete an ad set.

        Args:
            adset_id: AdSet ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If deletion fails
        """
        try:
            logger.info(f"Deleting ad set: {adset_id}")

            adset = AdSet(adset_id)
            adset.remote_delete()

            logger.info(f"Ad set deleted: {adset_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete ad set {adset_id}: {str(e)}")
            raise ValueError(f"AdSet deletion failed: {str(e)}")

    def get_adset(self, adset_id: str) -> Dict[str, Any]:
        """
        Get ad set details.

        Args:
            adset_id: AdSet ID

        Returns:
            AdSet data dictionary

        Raises:
            ValueError: If fetch fails
        """
        try:
            adset = AdSet(adset_id)
            adset_data = adset.api_get(fields=[
                AdSet.Field.id,
                AdSet.Field.name,
                AdSet.Field.campaign_id,
                AdSet.Field.status,
                AdSet.Field.daily_budget,
                AdSet.Field.lifetime_budget,
                AdSet.Field.optimization_goal,
                AdSet.Field.billing_event,
                AdSet.Field.targeting,
            ])

            return dict(adset_data)

        except Exception as e:
            logger.error(f"Failed to fetch ad set {adset_id}: {str(e)}")
            raise ValueError(f"AdSet fetch failed: {str(e)}")

    @staticmethod
    def build_targeting(
        geo_locations: Optional[List[str]] = None,
        age_min: int = 18,
        age_max: int = 65,
        genders: Optional[List[int]] = None,
        interests: Optional[List[Dict[str, str]]] = None,
        custom_audiences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build targeting spec for ad set.

        Args:
            geo_locations: List of country codes (e.g., ['US', 'CA'])
            age_min: Minimum age
            age_max: Maximum age
            genders: List of gender codes (1=male, 2=female)
            interests: List of interest IDs
            custom_audiences: List of custom audience IDs

        Returns:
            Targeting spec dictionary
        """
        targeting = {
            Targeting.Field.age_min: age_min,
            Targeting.Field.age_max: age_max,
        }

        # Geo locations
        if geo_locations:
            targeting[Targeting.Field.geo_locations] = {
                'countries': geo_locations
            }

        # Genders
        if genders:
            targeting[Targeting.Field.genders] = genders

        # Interests
        if interests:
            targeting[Targeting.Field.interests] = interests

        # Custom audiences
        if custom_audiences:
            targeting[Targeting.Field.custom_audiences] = [
                {'id': audience_id} for audience_id in custom_audiences
            ]

        return targeting
