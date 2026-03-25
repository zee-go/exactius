#!/usr/bin/env python3
"""
Exactius - Facebook Ads Automation Platform
Main entry point for campaign automation
"""

import argparse
import logging
import sys
from pathlib import Path

from config import Config
from auth import FacebookAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection(config: Config) -> bool:
    """Test Facebook API connection and authentication."""
    logger.info("Testing Facebook API connection...")

    try:
        auth = FacebookAuth(config)
        api = auth.get_api_instance()

        # Test API by fetching ad account info
        from facebook_business.adobjects.adaccount import AdAccount
        account = AdAccount(config.ad_account_id)
        account_info = account.api_get(fields=['name', 'account_id', 'currency'])

        logger.info(f"✓ Successfully connected to ad account: {account_info.get('name')}")
        logger.info(f"  Account ID: {account_info.get('account_id')}")
        logger.info(f"  Currency: {account_info.get('currency')}")

        return True

    except Exception as e:
        logger.error(f"✗ Connection test failed: {str(e)}")
        return False


def update_ad_sheet(config: Config, spreadsheet_id: str, sheet_name: str, days: int) -> bool:
    """Fetch new ads and update Google Sheet with preview links."""
    logger.info("Starting ad sheet update...")

    try:
        # Initialize Facebook API
        auth = FacebookAuth(config)
        auth.get_api_instance()

        # Get service account JSON for Sheets API
        if config.is_multi_account_mode():
            from src.secrets.manager import SecretManagerClient
            secrets = SecretManagerClient(config.google_cloud_project)
            shared = secrets.get_shared_credentials()
            service_account_json = shared['drive_service_account']
        else:
            import os
            sa_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if sa_path and Path(sa_path).exists():
                service_account_json = Path(sa_path).read_text()
            else:
                sa_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT')
                if not sa_json:
                    logger.error(
                        "No Google service account configured. Set either:\n"
                        "  GOOGLE_SERVICE_ACCOUNT_JSON (path to JSON file)\n"
                        "  GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT (JSON string)"
                    )
                    return False
                service_account_json = sa_json

        # Run the updater
        from src.automation.ad_sheet_updater import AdSheetUpdater
        updater = AdSheetUpdater(
            ad_account_id=config.ad_account_id,
            access_token=config.access_token,
            service_account_json=service_account_json,
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
        )

        result = updater.run(days=days)

        if result.success:
            logger.info(f"✓ Ad sheet update complete")
            logger.info(f"  Ads processed: {result.ads_processed}")
            logger.info(f"  Rows added: {result.rows_added}")
            if result.ads_skipped_duplicate > 0:
                logger.info(f"  Duplicates skipped: {result.ads_skipped_duplicate}")
            if result.ads_failed_preview > 0:
                logger.warning(f"  Preview failures: {result.ads_failed_preview}")
        else:
            logger.error(f"✗ Ad sheet update failed: {', '.join(result.errors)}")

        return result.success

    except Exception as e:
        logger.error(f"✗ Ad sheet update failed: {str(e)}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Exactius - Facebook Ads Automation Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test Facebook API connection and exit'
    )

    parser.add_argument(
        '--update-sheet',
        action='store_true',
        help='Fetch new ads and update Google Sheet with preview links'
    )

    parser.add_argument(
        '--spreadsheet-id',
        type=str,
        help='Google Sheets spreadsheet ID (overrides SPREADSHEET_ID env var)'
    )

    parser.add_argument(
        '--sheet-name',
        type=str,
        default=None,
        help='Sheet tab name (default: Sheet1)'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to look back for new ads (default: 7)'
    )

    parser.add_argument(
        '--account',
        type=str,
        help='Override ad account ID from environment'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level'
    )

    args = parser.parse_args()

    # Set log level if specified
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Load configuration
    try:
        config = Config()

        # Override ad account if specified
        if args.account:
            config.ad_account_id = args.account

        logger.info("Configuration loaded successfully")

    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)

    # Test connection if requested
    if args.test_connection:
        success = test_connection(config)
        sys.exit(0 if success else 1)

    # Update ad sheet if requested
    if args.update_sheet:
        spreadsheet_id = args.spreadsheet_id or config.spreadsheet_id
        if not spreadsheet_id:
            logger.error(
                "Spreadsheet ID required. Use --spreadsheet-id or set SPREADSHEET_ID env var."
            )
            sys.exit(1)

        sheet_name = args.sheet_name or config.sheet_name
        success = update_ad_sheet(config, spreadsheet_id, sheet_name, args.days)
        sys.exit(0 if success else 1)

    # Default: show help
    logger.info("Exactius Ads Automation Platform")
    logger.info("Use --update-sheet to sync new ads to Google Sheets.")
    logger.info("Use --test-connection to verify API access.")


if __name__ == '__main__':
    main()
