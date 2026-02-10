#!/usr/bin/env python3
"""
Example script: List all campaigns in your ad account
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config
from auth import FacebookAuth
from campaigns.manager import CampaignManager


def main():
    """List all campaigns."""
    print("Fetching campaigns from Facebook Ads Manager...\n")

    # Load configuration
    config = Config()

    # Initialize authentication
    auth = FacebookAuth(config)
    ad_account = auth.get_ad_account()

    # Create campaign manager
    manager = CampaignManager(ad_account)

    # Fetch campaigns
    campaigns = manager.get_campaigns()

    if not campaigns:
        print("No campaigns found.")
        return

    print(f"Found {len(campaigns)} campaigns:\n")

    # Print campaign details
    for campaign in campaigns:
        print(f"Name: {campaign.get('name')}")
        print(f"ID: {campaign.get('id')}")
        print(f"Status: {campaign.get('status')}")
        print(f"Objective: {campaign.get('objective')}")

        daily_budget = campaign.get('daily_budget')
        if daily_budget:
            print(f"Daily Budget: ${float(daily_budget) / 100:.2f}")

        lifetime_budget = campaign.get('lifetime_budget')
        if lifetime_budget:
            print(f"Lifetime Budget: ${float(lifetime_budget) / 100:.2f}")

        print("-" * 50)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
