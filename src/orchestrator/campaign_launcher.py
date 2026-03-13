"""
Campaign Launcher - Orchestrates the full campaign creation workflow.

Workflow:
1. Parse Drive URL and download assets
2. Validate assets against Meta specs
3. Upload assets to Meta Ad Library
4. Apply naming rules
5. Create campaign structure (Campaign → AdSet → Ads)
6. Handle rollback on errors

All campaigns start PAUSED for manual review.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

from src.drive.client import DriveClient, DriveAsset
from src.drive.parser import DriveURLParser
from src.assets.validator import AssetValidator
from src.naming.resolver import NamingResolver
from src.campaigns.manager import CampaignManager
from src.campaigns.adset_manager import AdSetManager
from src.campaigns.creative_manager import CreativeManager
from src.campaigns.ad_manager import AdManager

logger = logging.getLogger(__name__)


@dataclass
class LaunchResult:
    """Result of campaign launch operation."""
    success: bool
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    ad_ids: List[str] = field(default_factory=list)
    creative_ids: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'campaign_id': self.campaign_id,
            'adset_id': self.adset_id,
            'ad_ids': self.ad_ids,
            'creative_ids': self.creative_ids,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
        }


class CampaignLauncher:
    """Orchestrates campaign creation from Drive assets to Meta ads."""

    def __init__(
        self,
        account_config: Dict[str, Any],
        account_token: str,
        shared_credentials: Dict[str, str]
    ):
        """
        Initialize campaign launcher.

        Args:
            account_config: Account configuration from Secret Manager
            account_token: Meta access token for this account
            shared_credentials: Shared credentials (app_id, app_secret, drive SA)
        """
        self.account_config = account_config
        self.account_id = account_config['account_id']
        self.account_token = account_token
        self.shared_credentials = shared_credentials

        # Initialize Meta API
        FacebookAdsApi.init(
            app_id=shared_credentials['app_id'],
            app_secret=shared_credentials['app_secret'],
            access_token=account_token
        )

        # Initialize managers
        self.ad_account = AdAccount(self.account_id)
        self.campaign_manager = CampaignManager(self.ad_account)
        self.adset_manager = AdSetManager(self.account_id, account_token)
        self.creative_manager = CreativeManager(self.account_id, account_token)
        self.ad_manager = AdManager(self.account_id, account_token)

        # Initialize Drive client
        self.drive_client = DriveClient(shared_credentials['drive_service_account'])

        logger.info(f"Initialized CampaignLauncher for {self.account_id}")

    def launch_campaign(
        self,
        drive_url: str,
        campaign_type: str,
        context: Dict[str, Any],
        daily_budget: int,
        objective: str = 'LINK_CLICKS',
        preview_only: bool = False
    ) -> LaunchResult:
        """
        Launch a campaign from Drive assets.

        Args:
            drive_url: Google Drive folder or file URL
            campaign_type: Type of campaign (traffic_campaign, conversions_campaign, etc.)
            context: Variables for naming templates (product, audience, etc.)
            daily_budget: Daily budget in cents (e.g., 1000 = $10)
            objective: Campaign objective (LINK_CLICKS, CONVERSIONS, etc.)
            preview_only: If True, validate and preview without creating

        Returns:
            LaunchResult with campaign details or errors
        """
        result = LaunchResult(success=False)

        try:
            logger.info("=" * 70)
            logger.info(f"Starting campaign launch for {self.account_id}")
            logger.info(f"Campaign type: {campaign_type}")
            logger.info(f"Drive URL: {drive_url}")
            logger.info(f"Preview only: {preview_only}")
            logger.info("=" * 70)

            # Step 1: Download assets from Drive
            logger.info("\n[1/6] Downloading assets from Google Drive...")
            assets = self._download_assets(drive_url)
            result.metadata['asset_count'] = len(assets)
            logger.info(f"✓ Downloaded {len(assets)} asset(s)")

            if not assets:
                result.errors.append("No supported assets found in Drive folder")
                return result

            # Step 2: Validate assets
            logger.info("\n[2/6] Validating assets...")
            valid_assets, validation_warnings = self._validate_assets(assets)
            result.warnings.extend(validation_warnings)
            result.metadata['valid_asset_count'] = len(valid_assets)
            logger.info(f"✓ {len(valid_assets)}/{len(assets)} asset(s) passed validation")

            if not valid_assets:
                result.errors.append("No valid assets after validation")
                return result

            # Step 3: Initialize naming resolver
            logger.info("\n[3/6] Initializing naming resolver...")
            naming_resolver = NamingResolver(self.account_config, campaign_type)

            # Validate context has all required variables
            is_valid, missing = naming_resolver.validate_context(context)
            if not is_valid:
                result.errors.append(f"Missing required naming variables: {', '.join(missing)}")
                return result

            # Generate names
            names = naming_resolver.preview_names(context)
            result.metadata['names'] = names
            logger.info(f"✓ Generated names:")
            logger.info(f"  Campaign: {names['campaign']}")
            logger.info(f"  AdSet: {names['adset']}")
            logger.info(f"  Ad: {names['ad']}")

            # Preview mode: stop here
            if preview_only:
                result.success = True
                result.metadata['preview'] = True
                result.metadata['assets'] = [a.to_dict() for a in valid_assets]
                logger.info("\n✓ Preview mode - stopping before creation")
                return result

            # Step 4: Upload assets to Meta
            logger.info("\n[4/6] Uploading assets to Meta Ad Library...")
            uploaded_assets = self._upload_assets(valid_assets, result)
            logger.info(f"✓ Uploaded {len(uploaded_assets)} asset(s) to Meta")

            if not uploaded_assets:
                result.errors.append("Failed to upload assets to Meta")
                self._rollback(result)
                return result

            # Step 5: Create campaign structure
            logger.info("\n[5/6] Creating campaign structure...")

            # Create campaign (PAUSED)
            campaign_id = self._create_campaign(
                names['campaign'],
                objective,
                result
            )
            if not campaign_id:
                self._rollback(result)
                return result

            # Create ad set (PAUSED)
            adset_id = self._create_adset(
                campaign_id,
                names['adset'],
                daily_budget,
                result
            )
            if not adset_id:
                self._rollback(result)
                return result

            # Create ads from uploaded assets (PAUSED)
            ad_ids = self._create_ads(
                adset_id,
                names['ad'],
                uploaded_assets,
                context,
                result
            )
            if not ad_ids:
                self._rollback(result)
                return result

            # Step 6: Success!
            logger.info("\n[6/6] Campaign launch completed successfully!")
            logger.info(f"✓ Campaign ID: {campaign_id}")
            logger.info(f"✓ AdSet ID: {adset_id}")
            logger.info(f"✓ Ads created: {len(ad_ids)}")
            logger.info(f"✓ Status: PAUSED (ready for review)")

            result.success = True
            return result

        except Exception as e:
            logger.error(f"Campaign launch failed: {str(e)}", exc_info=True)
            result.errors.append(f"Unexpected error: {str(e)}")
            self._rollback(result)
            return result

    def _download_assets(self, drive_url: str) -> List[DriveAsset]:
        """Download assets from Drive."""
        try:
            # Parse URL
            resource_type, resource_id = DriveURLParser.parse(drive_url)

            if resource_type == 'folder':
                # Download folder
                assets = self.drive_client.download_folder(
                    resource_id,
                    filter_supported=True
                )
            else:
                # Download single file
                file_path = self.drive_client.download_file(resource_id)
                metadata = self.drive_client.get_file_metadata(resource_id)
                assets = [DriveAsset(
                    file_id=resource_id,
                    name=metadata['name'],
                    mime_type=metadata['mimeType'],
                    size=int(metadata.get('size', 0)),
                    local_path=file_path
                )]

            return assets

        except Exception as e:
            raise ValueError(f"Failed to download assets from Drive: {str(e)}")

    def _validate_assets(
        self,
        assets: List[DriveAsset]
    ) -> tuple[List[DriveAsset], List[str]]:
        """Validate assets against Meta specs."""
        valid_assets = []
        all_warnings = []

        for asset in assets:
            try:
                validation = AssetValidator.validate_file(
                    asset.local_path,
                    asset.mime_type
                )

                if validation['valid']:
                    valid_assets.append(asset)
                else:
                    logger.warning(f"Asset {asset.name} failed validation:")
                    for error in validation['errors']:
                        logger.warning(f"  - {error}")

                # Collect warnings
                all_warnings.extend([
                    f"{asset.name}: {w}" for w in validation['warnings']
                ])

            except Exception as e:
                logger.error(f"Validation error for {asset.name}: {str(e)}")
                continue

        return valid_assets, all_warnings

    def _upload_single_asset(
        self,
        asset: DriveAsset,
        page_id: str
    ) -> Dict[str, Any] | None:
        """Upload a single asset to Meta Ad Library. Returns metadata dict or None on failure."""
        try:
            if self.drive_client.is_image(asset.mime_type):
                image_hash = self.creative_manager.upload_image(asset.local_path)
                creative_id = self.creative_manager.create_image_creative(
                    image_hash=image_hash,
                    creative_name=f"Creative_{asset.name}",
                    page_id=page_id
                )
                return {
                    'asset': asset,
                    'creative_id': creative_id,
                    'type': 'image',
                    'hash': image_hash,
                }

            elif self.drive_client.is_video(asset.mime_type):
                video_id = self.creative_manager.upload_video(asset.local_path)
                creative_id = self.creative_manager.create_video_creative(
                    video_id=video_id,
                    creative_name=f"Creative_{asset.name}",
                    page_id=page_id
                )
                return {
                    'asset': asset,
                    'creative_id': creative_id,
                    'type': 'video',
                    'video_id': video_id,
                }

        except Exception as e:
            logger.error(f"Failed to upload {asset.name}: {str(e)}")

        return None

    def _upload_assets(
        self,
        assets: List[DriveAsset],
        result: LaunchResult,
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        """Upload assets to Meta Ad Library in parallel."""
        page_id = self.account_config.get('meta', {}).get('page_id')

        if not page_id:
            raise ValueError("Page ID not configured in account settings")

        uploaded = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._upload_single_asset, asset, page_id): asset
                for asset in assets
            }

            for future in as_completed(futures):
                asset = futures[future]
                asset_result = future.result()
                if asset_result is not None:
                    result.creative_ids.append(asset_result['creative_id'])
                    uploaded.append(asset_result)
                    logger.info(f"Uploaded {asset.name} → creative {asset_result['creative_id']}")

        return uploaded

    def _create_campaign(
        self,
        campaign_name: str,
        objective: str,
        result: LaunchResult
    ) -> Optional[str]:
        """Create campaign."""
        try:
            campaign = self.campaign_manager.create_campaign(
                name=campaign_name,
                objective=objective,
                status='PAUSED'
            )
            campaign_id = campaign['id']
            result.campaign_id = campaign_id
            logger.info(f"✓ Created campaign: {campaign_id}")
            return campaign_id

        except Exception as e:
            logger.error(f"Failed to create campaign: {str(e)}")
            result.errors.append(f"Campaign creation failed: {str(e)}")
            return None

    def _create_adset(
        self,
        campaign_id: str,
        adset_name: str,
        daily_budget: int,
        result: LaunchResult
    ) -> Optional[str]:
        """Create ad set."""
        try:
            # Get targeting from account defaults
            defaults = self.account_config.get('defaults', {})
            geo_locations = defaults.get('geo_locations', ['US'])
            age_min = defaults.get('age_min', 18)
            age_max = defaults.get('age_max', 65)

            targeting = AdSetManager.build_targeting(
                geo_locations=geo_locations,
                age_min=age_min,
                age_max=age_max
            )

            adset_id = self.adset_manager.create_adset(
                campaign_id=campaign_id,
                adset_name=adset_name,
                daily_budget=daily_budget,
                targeting=targeting,
                status='PAUSED'
            )

            result.adset_id = adset_id
            logger.info(f"✓ Created ad set: {adset_id}")
            return adset_id

        except Exception as e:
            logger.error(f"Failed to create ad set: {str(e)}")
            result.errors.append(f"AdSet creation failed: {str(e)}")
            return None

    def _create_ads(
        self,
        adset_id: str,
        ad_name_template: str,
        uploaded_assets: List[Dict[str, Any]],
        context: Dict[str, Any],
        result: LaunchResult
    ) -> List[str]:
        """Create ads from uploaded assets."""
        ad_ids = []

        for i, asset_data in enumerate(uploaded_assets, 1):
            try:
                # Generate unique ad name
                asset_context = {**context, 'variant': f"{i:02d}"}
                ad_name = ad_name_template + f"_{i:02d}"

                # Create ad
                ad_id = self.ad_manager.create_ad(
                    adset_id=adset_id,
                    creative_id=asset_data['creative_id'],
                    ad_name=ad_name,
                    status='PAUSED'
                )

                ad_ids.append(ad_id)
                logger.info(f"✓ Created ad {i}/{len(uploaded_assets)}: {ad_id}")

            except Exception as e:
                logger.error(f"Failed to create ad {i}: {str(e)}")
                result.errors.append(f"Ad {i} creation failed: {str(e)}")
                continue

        result.ad_ids = ad_ids
        return ad_ids

    def _rollback(self, result: LaunchResult):
        """Rollback created entities on error."""
        logger.warning("⚠️  Rolling back created entities...")

        # Delete ads (reverse order)
        for ad_id in reversed(result.ad_ids):
            try:
                self.ad_manager.delete_ad(ad_id)
                logger.info(f"  Deleted ad: {ad_id}")
            except Exception as e:
                logger.error(f"  Failed to delete ad {ad_id}: {str(e)}")

        # Delete ad set
        if result.adset_id:
            try:
                self.adset_manager.delete_adset(result.adset_id)
                logger.info(f"  Deleted ad set: {result.adset_id}")
            except Exception as e:
                logger.error(f"  Failed to delete ad set: {str(e)}")

        # Delete campaign
        if result.campaign_id:
            try:
                self.campaign_manager.delete_campaign(result.campaign_id)
                logger.info(f"  Deleted campaign: {result.campaign_id}")
            except Exception as e:
                logger.error(f"  Failed to delete campaign: {str(e)}")

        # Delete creatives
        for creative_id in reversed(result.creative_ids):
            try:
                self.creative_manager.delete_creative(creative_id)
                logger.info(f"  Deleted creative: {creative_id}")
            except Exception as e:
                logger.error(f"  Failed to delete creative {creative_id}: {str(e)}")

        logger.warning("✓ Rollback completed")
