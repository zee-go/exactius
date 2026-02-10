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

    # Main automation logic would go here
    logger.info("Exactius Ads Automation Platform")
    logger.info("No automation workflows implemented yet.")
    logger.info("Use --test-connection to verify API access.")


if __name__ == '__main__':
    main()
