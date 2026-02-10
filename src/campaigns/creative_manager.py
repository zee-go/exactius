"""
Meta API Creative Manager.

Handles uploading images and videos to Meta Ad Library and creating ad creatives.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.advideo import AdVideo
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.api import FacebookAdsApi

logger = logging.getLogger(__name__)


class CreativeManager:
    """Manages creative assets and ad creatives in Meta Ads."""

    def __init__(self, ad_account_id: str, access_token: str):
        """
        Initialize creative manager.

        Args:
            ad_account_id: Meta ad account ID (format: act_123456789)
            access_token: Meta access token for this account
        """
        self.ad_account_id = ad_account_id
        self.access_token = access_token
        self.ad_account = AdAccount(ad_account_id)

        logger.info(f"Initialized CreativeManager for {ad_account_id}")

    def upload_image(self, image_path: Path) -> str:
        """
        Upload image to Meta Ad Library.

        Args:
            image_path: Path to image file

        Returns:
            Image hash (used to reference image in creatives)

        Raises:
            ValueError: If upload fails
        """
        try:
            logger.info(f"Uploading image: {image_path.name}")

            # Create AdImage object
            image = AdImage(parent_id=self.ad_account_id)

            # Upload image
            image[AdImage.Field.filename] = str(image_path)
            image.remote_create()

            # Get hash
            image_hash = image[AdImage.Field.hash]
            logger.info(f"Image uploaded successfully. Hash: {image_hash}")

            return image_hash

        except Exception as e:
            logger.error(f"Failed to upload image {image_path.name}: {str(e)}")
            raise ValueError(f"Image upload failed: {str(e)}")

    def upload_video(
        self,
        video_path: Path,
        poll_interval: int = 5,
        max_wait: int = 300
    ) -> str:
        """
        Upload video to Meta Ad Library (async operation).

        Args:
            video_path: Path to video file
            poll_interval: Seconds between upload status checks
            max_wait: Maximum seconds to wait for upload completion

        Returns:
            Video ID (used to reference video in creatives)

        Raises:
            ValueError: If upload fails or times out
        """
        try:
            logger.info(f"Uploading video: {video_path.name}")

            # Create AdVideo object
            video = AdVideo(parent_id=self.ad_account_id)

            # Upload video (async)
            video[AdVideo.Field.filepath] = str(video_path)
            video.remote_create()

            # Get video ID
            video_id = video[AdVideo.Field.id]
            logger.info(f"Video upload initiated. ID: {video_id}")

            # Poll for upload completion
            start_time = time.time()
            while True:
                # Check if timeout
                elapsed = time.time() - start_time
                if elapsed > max_wait:
                    raise ValueError(
                        f"Video upload timed out after {max_wait} seconds. "
                        f"Video ID: {video_id}"
                    )

                # Fetch video status
                video_status = video.api_get(fields=[AdVideo.Field.status])
                status = video_status.get(AdVideo.Field.status, {})

                processing_phase = status.get('processing_phase')
                logger.debug(f"Video processing phase: {processing_phase}")

                # Check if ready
                if processing_phase == 'ready':
                    logger.info(f"Video upload completed. ID: {video_id}")
                    return video_id

                # Check if failed
                if processing_phase == 'error':
                    error_msg = status.get('uploading_phase', {}).get('errors', 'Unknown error')
                    raise ValueError(f"Video upload failed: {error_msg}")

                # Wait before next check
                logger.debug(f"Waiting {poll_interval}s for video processing...")
                time.sleep(poll_interval)

        except Exception as e:
            logger.error(f"Failed to upload video {video_path.name}: {str(e)}")
            raise ValueError(f"Video upload failed: {str(e)}")

    def create_image_creative(
        self,
        image_hash: str,
        creative_name: str,
        page_id: str,
        message: Optional[str] = None,
        link: Optional[str] = None,
        call_to_action: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create ad creative with image.

        Args:
            image_hash: Image hash from upload_image()
            creative_name: Name for the creative
            page_id: Facebook page ID
            message: Ad text/message
            link: Destination URL
            call_to_action: CTA button config (type, value)

        Returns:
            Creative ID

        Raises:
            ValueError: If creative creation fails
        """
        try:
            logger.info(f"Creating image creative: {creative_name}")

            # Build object story spec
            object_story_spec = {
                'page_id': page_id,
                'link_data': {
                    'image_hash': image_hash,
                }
            }

            if message:
                object_story_spec['link_data']['message'] = message

            if link:
                object_story_spec['link_data']['link'] = link

            if call_to_action:
                object_story_spec['link_data']['call_to_action'] = call_to_action

            # Create creative
            creative = AdCreative(parent_id=self.ad_account_id)
            creative.update({
                AdCreative.Field.name: creative_name,
                AdCreative.Field.object_story_spec: object_story_spec,
            })
            creative.remote_create()

            creative_id = creative[AdCreative.Field.id]
            logger.info(f"Image creative created. ID: {creative_id}")

            return creative_id

        except Exception as e:
            logger.error(f"Failed to create image creative: {str(e)}")
            raise ValueError(f"Creative creation failed: {str(e)}")

    def create_video_creative(
        self,
        video_id: str,
        creative_name: str,
        page_id: str,
        message: Optional[str] = None,
        call_to_action: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create ad creative with video.

        Args:
            video_id: Video ID from upload_video()
            creative_name: Name for the creative
            page_id: Facebook page ID
            message: Ad text/message
            call_to_action: CTA button config

        Returns:
            Creative ID

        Raises:
            ValueError: If creative creation fails
        """
        try:
            logger.info(f"Creating video creative: {creative_name}")

            # Build object story spec
            object_story_spec = {
                'page_id': page_id,
                'video_data': {
                    'video_id': video_id,
                }
            }

            if message:
                object_story_spec['video_data']['message'] = message

            if call_to_action:
                object_story_spec['video_data']['call_to_action'] = call_to_action

            # Create creative
            creative = AdCreative(parent_id=self.ad_account_id)
            creative.update({
                AdCreative.Field.name: creative_name,
                AdCreative.Field.object_story_spec: object_story_spec,
            })
            creative.remote_create()

            creative_id = creative[AdCreative.Field.id]
            logger.info(f"Video creative created. ID: {creative_id}")

            return creative_id

        except Exception as e:
            logger.error(f"Failed to create video creative: {str(e)}")
            raise ValueError(f"Creative creation failed: {str(e)}")

    def delete_image(self, image_hash: str) -> bool:
        """
        Delete image from Ad Library.

        Args:
            image_hash: Image hash to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If deletion fails
        """
        try:
            logger.info(f"Deleting image: {image_hash}")

            image = AdImage(parent_id=self.ad_account_id)
            image[AdImage.Field.hash] = image_hash
            image.remote_delete()

            logger.info(f"Image deleted: {image_hash}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete image {image_hash}: {str(e)}")
            raise ValueError(f"Image deletion failed: {str(e)}")

    def delete_video(self, video_id: str) -> bool:
        """
        Delete video from Ad Library.

        Args:
            video_id: Video ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If deletion fails
        """
        try:
            logger.info(f"Deleting video: {video_id}")

            video = AdVideo(video_id)
            video.remote_delete()

            logger.info(f"Video deleted: {video_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete video {video_id}: {str(e)}")
            raise ValueError(f"Video deletion failed: {str(e)}")

    def delete_creative(self, creative_id: str) -> bool:
        """
        Delete ad creative.

        Args:
            creative_id: Creative ID to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If deletion fails
        """
        try:
            logger.info(f"Deleting creative: {creative_id}")

            creative = AdCreative(creative_id)
            creative.remote_delete()

            logger.info(f"Creative deleted: {creative_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete creative {creative_id}: {str(e)}")
            raise ValueError(f"Creative deletion failed: {str(e)}")
