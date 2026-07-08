"""
One-time script to register the ClickUp webhook for taskStatusUpdated events.

Usage:
    CLICKUP_API_TOKEN=pk_... python scripts/register_clickup_webhook.py \
        --team-id <your-team-id> \
        --endpoint https://your-server.com/api/clickup/webhook \
        --secret <shared-webhook-secret>

Find your team ID at: https://app.clickup.com/<team-id>/
"""

import argparse
import os
import sys

import requests

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


def main():
    parser = argparse.ArgumentParser(description="Register ClickUp webhook")
    parser.add_argument("--team-id", required=True, help="ClickUp workspace/team ID")
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Public webhook URL, e.g. https://yourserver.com/api/clickup/webhook",
    )
    parser.add_argument(
        "--secret",
        default=os.getenv("CLICKUP_WEBHOOK_SECRET", ""),
        help="Shared secret for HMAC signature verification (recommended)",
    )
    args = parser.parse_args()

    api_token = os.getenv("CLICKUP_API_TOKEN")
    if not api_token:
        print("ERROR: CLICKUP_API_TOKEN environment variable is required")
        sys.exit(1)

    payload = {
        "endpoint": args.endpoint,
        "events": ["taskStatusUpdated"],
    }
    if args.secret:
        payload["secret"] = args.secret

    resp = requests.post(
        f"{CLICKUP_API_BASE}/team/{args.team_id}/webhook",
        headers={"Authorization": api_token, "Content-Type": "application/json"},
        json=payload,
    )

    if not resp.ok:
        print(f"ERROR: {resp.status_code} — {resp.text}")
        sys.exit(1)

    data = resp.json()
    webhook_id = data.get("id") or data.get("webhook", {}).get("id")
    print("Webhook registered successfully!")
    print(f"  Webhook ID : {webhook_id}")
    print(f"  Endpoint   : {args.endpoint}")
    print(f"  Events     : taskStatusUpdated")
    print()
    print("To delete later:")
    print(f"  DELETE https://api.clickup.com/api/v2/webhook/{webhook_id}")


if __name__ == "__main__":
    main()
