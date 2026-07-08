"""
Inspect the custom fields on a ClickUp list — use this to set up and verify the
"Meta Ad Account" dropdown that drives per-task account selection.

It prints each custom field's name and type, and for dropdowns lists the option
labels. The dropdown option labels must match your Meta account short names
(e.g. "nike") or ad account IDs (e.g. "act_123456789") so the sync can resolve
them via AccountManager.

Usage:
    CLICKUP_API_TOKEN=pk_... python scripts/list_clickup_fields.py --list-id <list_id>
"""

import argparse
import os
import sys

import requests

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


def main():
    parser = argparse.ArgumentParser(description="List ClickUp custom fields for a list")
    parser.add_argument("--list-id", required=True, help="ClickUp list ID")
    args = parser.parse_args()

    api_token = os.getenv("CLICKUP_API_TOKEN")
    if not api_token:
        print("ERROR: CLICKUP_API_TOKEN environment variable is required")
        sys.exit(1)

    resp = requests.get(
        f"{CLICKUP_API_BASE}/list/{args.list_id}/field",
        headers={"Authorization": api_token},
    )
    if not resp.ok:
        print(f"ERROR: {resp.status_code} — {resp.text}")
        sys.exit(1)

    fields = resp.json().get("fields", [])
    if not fields:
        print("No custom fields found on this list.")
        return

    print(f"Custom fields on list {args.list_id}:\n")
    for field in fields:
        name = field.get("name")
        ftype = field.get("type")
        print(f"- {name!r}  (type: {ftype})")
        if ftype == "drop_down":
            options = (field.get("type_config") or {}).get("options", [])
            if not options:
                print("    (no options defined)")
            for opt in options:
                print(f"    [{opt.get('orderindex')}] {opt.get('name')!r}  (id: {opt.get('id')})")
    print()
    print("For account selection: create a dropdown named 'Meta Ad Account' (or set")
    print("CLICKUP_ACCOUNT_FIELD) whose option labels are your account short names / IDs.")


if __name__ == "__main__":
    main()
