#!/usr/bin/env python3
"""
Example script: Get insights for a specific campaign
Usage: python scripts/get_campaign_insights.py <campaign_id>
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config
from auth import FacebookAuth
from reporting.analytics import CampaignAnalytics


def main():
    """Get campaign insights."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/get_campaign_insights.py <campaign_id>")
        print("\nExample: python scripts/get_campaign_insights.py 123456789")
        sys.exit(1)

    campaign_id = sys.argv[1]

    print(f"Fetching insights for campaign {campaign_id}...\n")

    # Load configuration
    config = Config()

    # Initialize authentication
    auth = FacebookAuth(config)
    ad_account = auth.get_ad_account()

    # Create analytics instance
    analytics = CampaignAnalytics(ad_account)

    # Get insights for last 7 days
    date_range = {
        'since': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'until': datetime.now().strftime('%Y-%m-%d')
    }

    insights = analytics.get_campaign_insights(
        campaign_id=campaign_id,
        date_range=date_range
    )

    if not insights:
        print("No insights found for this campaign.")
        return

    # Print insights
    print(f"Campaign Insights ({date_range['since']} to {date_range['until']}):\n")

    metrics = [
        ('Impressions', 'impressions'),
        ('Clicks', 'clicks'),
        ('Spend', 'spend'),
        ('CPC', 'cpc'),
        ('CTR', 'ctr'),
        ('Conversions', 'conversions'),
        ('Cost per Conversion', 'cost_per_conversion')
    ]

    for label, field in metrics:
        value = insights.get(field, 'N/A')
        if value != 'N/A' and field in ['spend', 'cpc', 'cost_per_conversion']:
            value = f"${float(value):.2f}"
        elif value != 'N/A' and field == 'ctr':
            value = f"{float(value):.2f}%"
        print(f"{label}: {value}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
