"""
Ad Sheet Updater - Orchestrates fetching ad previews and writing to Google Sheets.

Workflow:
1. Load last run timestamp (for "since last run" tracking)
2. Fetch new ads with shareable preview links from Meta API
3. Deduplicate against existing rows in the Google Sheet
4. Append new rows to the sheet
5. Save current timestamp as last run
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.sheets.client import SheetsClient
from src.automation.ad_preview_fetcher import AdPreviewFetcher, AdPreviewData

logger = logging.getLogger(__name__)

# Sheet column headers
SHEET_HEADERS = [
    'Ad Name',
    'Ad ID',
    'Campaign',
    'FB Preview Link',
    'IG Preview Link',
    'Created',
    'Added',
]

# Default state file location
STATE_DIR = Path.home() / '.exactius'
STATE_FILE = STATE_DIR / 'last_sheet_update.json'


@dataclass
class UpdateResult:
    """Result of an ad sheet update operation."""
    success: bool
    rows_added: int = 0
    ads_processed: int = 0
    ads_skipped_duplicate: int = 0
    ads_failed_preview: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'rows_added': self.rows_added,
            'ads_processed': self.ads_processed,
            'ads_skipped_duplicate': self.ads_skipped_duplicate,
            'ads_failed_preview': self.ads_failed_preview,
            'errors': self.errors,
        }


class AdSheetUpdater:
    """Orchestrates fetching ad previews and updating a Google Sheet."""

    def __init__(
        self,
        ad_account_id: str,
        access_token: str,
        sheets_client: SheetsClient,
        spreadsheet_id: str,
        sheet_name: str = 'Sheet1',
    ):
        """
        Initialize the updater.

        Args:
            ad_account_id: Meta ad account ID (format: act_123456789)
            access_token: Meta access token
            sheets_client: Authenticated SheetsClient instance
            spreadsheet_id: Target Google Sheets spreadsheet ID
            sheet_name: Sheet tab name (default: Sheet1)
        """
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

        self.fetcher = AdPreviewFetcher(ad_account_id, access_token)
        self.sheets = sheets_client

        logger.info(
            f"Initialized AdSheetUpdater for {ad_account_id} "
            f"-> spreadsheet {spreadsheet_id}"
        )

    def run(self, days: int = 7, since: Optional[datetime] = None) -> UpdateResult:
        """
        Run the full update workflow.

        Args:
            days: Number of days to look back (fallback if no last run or since)
            since: Override start date (takes priority over last run timestamp)

        Returns:
            UpdateResult with summary of what happened
        """
        errors = []

        try:
            # 1. Determine the start date
            if since is None:
                since = self._load_last_run()

            # 2. Ensure header row exists
            self.sheets.ensure_header_row(
                self.spreadsheet_id,
                self.sheet_name,
                SHEET_HEADERS,
            )

            # 3. Get existing ad IDs from sheet for deduplication
            existing_ids = self._get_existing_ad_ids()
            logger.info(f"Found {len(existing_ids)} existing ad(s) in sheet")

            # 4. Fetch new ads with preview links
            ads = self.fetcher.fetch_ads_with_previews(since=since, days=days)

            # 5. Filter out duplicates
            new_ads = [ad for ad in ads if ad.ad_id not in existing_ids]
            skipped = len(ads) - len(new_ads)

            if skipped > 0:
                logger.info(f"Skipping {skipped} ad(s) already in sheet")

            # 6. Count preview failures
            failed_preview = sum(
                1 for ad in new_ads
                if not ad.facebook_preview_url and not ad.instagram_preview_url
            )

            # 7. Format and append rows
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            rows = [ad.to_row(added_time=now) for ad in new_ads]

            rows_added = 0
            if rows:
                range_name = f'{self.sheet_name}!A:G'
                rows_added = self.sheets.append_rows(
                    self.spreadsheet_id,
                    range_name,
                    rows,
                )

            # 8. Save last run timestamp
            self._save_last_run()

            return UpdateResult(
                success=True,
                rows_added=rows_added,
                ads_processed=len(ads),
                ads_skipped_duplicate=skipped,
                ads_failed_preview=failed_preview,
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Ad sheet update failed: {str(e)}")
            errors.append(str(e))
            return UpdateResult(success=False, errors=errors)

    def _get_existing_ad_ids(self) -> set:
        """
        Read existing ad IDs from column B of the sheet.

        Returns:
            Set of ad IDs already present in the sheet
        """
        try:
            range_name = f'{self.sheet_name}!B:B'
            rows = self.sheets.get_sheet_values(self.spreadsheet_id, range_name)

            # Skip header row, collect ad IDs
            ids = set()
            for row in rows[1:]:  # skip header
                if row:
                    ids.add(row[0])
            return ids

        except Exception as e:
            logger.warning(f"Could not read existing ad IDs: {str(e)}")
            return set()

    def _load_last_run(self) -> Optional[datetime]:
        """
        Load the last run timestamp from state file.

        Returns:
            Last run datetime, or None if no previous run
        """
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text())
                timestamp = data.get('last_run')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    logger.info(f"Last run was at {dt.isoformat()}")
                    return dt
        except Exception as e:
            logger.warning(f"Could not load last run timestamp: {str(e)}")

        return None

    def _save_last_run(self) -> None:
        """Save the current timestamp as last run."""
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                'last_run': datetime.now(timezone.utc).isoformat(),
                'spreadsheet_id': self.spreadsheet_id,
            }
            STATE_FILE.write_text(json.dumps(data, indent=2))
            logger.info("Saved last run timestamp")
        except Exception as e:
            logger.warning(f"Could not save last run timestamp: {str(e)}")
