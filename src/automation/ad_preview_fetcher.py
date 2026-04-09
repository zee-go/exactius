"""
Facebook Ad Preview Fetcher.

Fetches recently created ads from a Meta ad account and generates
shareable preview links for Facebook and Instagram placements.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.exceptions import FacebookRequestError

logger = logging.getLogger(__name__)


@dataclass
class AdPreviewData:
    """Data for a single ad with preview links."""
    ad_id: str
    ad_name: str
    created_time: str
    facebook_preview_url: Optional[str] = None
    instagram_preview_url: Optional[str] = None
    campaign_name: Optional[str] = None

    def to_row(self, added_time: Optional[str] = None) -> List[str]:
        """Format as a spreadsheet row."""
        return [
            self.ad_name,
            self.ad_id,
            self.campaign_name or '',
            self.facebook_preview_url or '',
            self.instagram_preview_url or '',
            self.created_time,
            added_time or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        ]


class AdPreviewFetcher:
    """Fetches ads and generates shareable preview links."""

    # Rate limit: pause between preview requests to avoid hitting limits
    PREVIEW_DELAY_SECONDS = 1.0
    MAX_RETRIES = 3

    def __init__(self, ad_account_id: str, access_token: str):
        """
        Initialize preview fetcher.

        Args:
            ad_account_id: Meta ad account ID (format: act_123456789)
            access_token: Meta access token
        """
        self.ad_account_id = ad_account_id
        self.access_token = access_token
        self.ad_account = AdAccount(ad_account_id)
        logger.info(f"Initialized AdPreviewFetcher for {ad_account_id}")

    def get_recent_ads(
        self,
        since: Optional[datetime] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Fetch ads created since a given date.

        Args:
            since: Fetch ads created after this datetime. If None, uses days param.
            days: Number of days to look back (used if since is None)

        Returns:
            List of ad data dictionaries
        """
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(days=days)

        since_str = since.strftime('%Y-%m-%d')
        until_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        logger.info(f"Fetching ads created between {since_str} and {until_str}")

        try:
            ads = self.ad_account.get_ads(
                fields=[
                    Ad.Field.id,
                    Ad.Field.name,
                    Ad.Field.created_time,
                    Ad.Field.status,
                    Ad.Field.creative,
                    'campaign{name}',
                ],
                params={
                    'time_range': {
                        'since': since_str,
                        'until': until_str,
                    },
                    'effective_status': [
                        'ACTIVE',
                        'PAUSED',
                        'PENDING_REVIEW',
                        'IN_PROCESS',
                    ],
                }
            )

            ad_list = []
            for ad in ads:
                ad_data = dict(ad)
                # Filter by created_time >= since
                created = datetime.fromisoformat(
                    ad_data.get('created_time', '').replace('+0000', '+00:00')
                )
                if created >= since.replace(tzinfo=timezone.utc) if since.tzinfo is None else since:
                    ad_list.append(ad_data)

            logger.info(f"Found {len(ad_list)} ad(s) created since {since_str}")
            return ad_list

        except FacebookRequestError as e:
            logger.error(f"Failed to fetch ads: {e.api_error_message()}")
            raise ValueError(f"Failed to fetch ads: {e.api_error_message()}")
        except Exception as e:
            logger.error(f"Failed to fetch ads: {str(e)}")
            raise ValueError(f"Failed to fetch ads: {str(e)}")

    def get_preview_link(self, ad_id: str, ad_format: str) -> Optional[str]:
        """
        Generate a shareable preview link for an ad.

        Args:
            ad_id: Facebook ad ID
            ad_format: Preview format (e.g., 'DESKTOP_FEED_STANDARD', 'INSTAGRAM_STANDARD')

        Returns:
            Shareable preview URL, or None if generation fails
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                ad = Ad(ad_id)
                previews = ad.get_ad_previews(params={
                    'ad_format': ad_format,
                })

                if previews:
                    preview = previews[0]
                    # The preview body contains an iframe with the preview URL
                    body = preview.get('body', '')
                    # Extract the shareable link from the iframe src
                    url = self._extract_preview_url(body)
                    if url:
                        return url

                logger.warning(f"No preview generated for ad {ad_id} format {ad_format}")
                return None

            except FacebookRequestError as e:
                error_code = e.api_error_code()
                # Rate limit error - back off and retry
                if error_code in (4, 17, 32, 613):
                    wait_time = (2 ** attempt) * self.PREVIEW_DELAY_SECONDS
                    logger.warning(
                        f"Rate limited on ad {ad_id}, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(wait_time)
                    continue
                logger.error(f"Preview generation failed for ad {ad_id}: {e.api_error_message()}")
                return None
            except Exception as e:
                logger.error(f"Preview generation failed for ad {ad_id}: {str(e)}")
                return None

        logger.error(f"Max retries exceeded for ad {ad_id} format {ad_format}")
        return None

    def _extract_preview_url(self, iframe_html: str) -> Optional[str]:
        """
        Extract the preview URL from an iframe HTML string.

        The Facebook Ad Preview API returns HTML containing an iframe.
        The iframe src is the shareable preview URL.

        Args:
            iframe_html: HTML string from preview API

        Returns:
            Extracted URL or None
        """
        if not iframe_html:
            return None

        # Look for src attribute in iframe
        import re
        match = re.search(r'src="([^"]+)"', iframe_html)
        if match:
            url = match.group(1)
            # Unescape HTML entities
            url = url.replace('&amp;', '&')
            return url

        return None

    def fetch_ads_with_previews(
        self,
        since: Optional[datetime] = None,
        days: int = 7
    ) -> List[AdPreviewData]:
        """
        Fetch recent ads and generate preview links for each.

        Args:
            since: Fetch ads created after this datetime
            days: Number of days to look back (used if since is None)

        Returns:
            List of AdPreviewData with preview URLs populated
        """
        ads = self.get_recent_ads(since=since, days=days)
        results = []

        for i, ad_data in enumerate(ads):
            ad_id = ad_data.get('id', '')
            ad_name = ad_data.get('name', '')
            created_time = ad_data.get('created_time', '')

            # Extract campaign name from nested object
            campaign = ad_data.get('campaign', {})
            campaign_name = campaign.get('name', '') if isinstance(campaign, dict) else ''

            logger.info(f"Generating previews for ad {i + 1}/{len(ads)}: {ad_name}")

            # Get Facebook preview
            fb_url = self.get_preview_link(ad_id, 'DESKTOP_FEED_STANDARD')

            # Small delay between requests to respect rate limits
            time.sleep(self.PREVIEW_DELAY_SECONDS)

            # Get Instagram preview
            ig_url = self.get_preview_link(ad_id, 'INSTAGRAM_STANDARD')

            if i < len(ads) - 1:
                time.sleep(self.PREVIEW_DELAY_SECONDS)

            results.append(AdPreviewData(
                ad_id=ad_id,
                ad_name=ad_name,
                created_time=created_time,
                facebook_preview_url=fb_url,
                instagram_preview_url=ig_url,
                campaign_name=campaign_name,
            ))

        logger.info(
            f"Generated previews for {len(results)} ad(s). "
            f"FB links: {sum(1 for r in results if r.facebook_preview_url)}, "
            f"IG links: {sum(1 for r in results if r.instagram_preview_url)}"
        )
        return results
