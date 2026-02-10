#!/usr/bin/env python3
"""
Example script: Create a new campaign (starts PAUSED for safety)
This is a minimal example - in production you'd want to add ad sets and ads too.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config
from auth import FacebookAuth
from campaigns.manager import CampaignManager


def main():
    """Create a test campaign."""
    print("Creating a new campaign...\n")

    # Load configuration
    config = Config()

    # Initialize authentication
    auth = FacebookAuth(config)
    ad_account = auth.get_ad_account()

    # Create campaign manager
    manager = CampaignManager(ad_account)

    # Campaign parameters
    campaign_name = "Test Campaign (Created via API)"
    objective = "OUTCOME_TRAFFIC"  # Common objective for website traffic

    # Ask for confirmation
    print(f"Campaign Name: {campaign_name}")
    print(f"Objective: {objective}")
    print(f"Status: PAUSED (for safety)")
    print(f"\nThis campaign will be created in your ad account: {config.ad_account_id}")

    response = input("\nDo you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        print("Campaign creation cancelled.")
        return

    # Create campaign
    campaign = manager.create_campaign(
        name=campaign_name,
        objective=objective,
        status='PAUSED'
    )

    print(f"\n✓ Campaign created successfully!")
    print(f"Campaign ID: {campaign['id']}")
    print(f"\nNote: Campaign is PAUSED. You need to:")
    print("1. Add ad sets (targeting, budget, schedule)")
    print("2. Add ads (creative, copy)")
    print("3. Activate the campaign in Facebook Ads Manager")
    print(f"\nView in Ads Manager: https://business.facebook.com/adsmanager/manage/campaigns?act={config.ad_account_id.replace('act_', '')}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
