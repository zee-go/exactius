#!/usr/bin/env python3
"""
One-time OAuth setup script for Google Sheets.

Usage:
    1. Run this script — it prints an authorization URL and saves PKCE state
    2. Visit the URL in your browser and authorize
    3. Copy the authorization code from the browser
    4. Run again with the code: python scripts/setup_sheets_oauth.py <CODE>
"""

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CLIENT_SECRETS_PATH = Path.home() / '.exactius' / 'client_secret.json'
TOKEN_PATH = Path.home() / '.exactius' / 'sheets_token.json'
FLOW_STATE_PATH = Path.home() / '.exactius' / 'oauth_flow_state.json'


def main():
    # Check if token already exists and is valid
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds and creds.valid:
            print("Already authenticated! Token is valid.")
            return
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
            print("Token refreshed successfully!")
            return

    if not CLIENT_SECRETS_PATH.exists():
        print(f"ERROR: Client secrets not found at {CLIENT_SECRETS_PATH}")
        sys.exit(1)

    if len(sys.argv) < 2:
        # Step 1: Generate auth URL and save flow state for step 2
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_PATH), SCOPES
        )
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')

        # Save the code verifier so step 2 can use it
        flow_state = {
            'state': state,
            'code_verifier': flow.code_verifier,
        }
        FLOW_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FLOW_STATE_PATH.write_text(json.dumps(flow_state))

        print("\n=== Google Sheets OAuth Setup ===\n")
        print("1. Visit this URL in your browser:\n")
        print(auth_url)
        print("\n2. Authorize and copy the code shown")
        print("3. Run again with the code:\n")
        print(f"   python scripts/setup_sheets_oauth.py YOUR_CODE_HERE\n")
    else:
        # Step 2: Exchange code for token using saved flow state
        code = sys.argv[1].strip()

        if not FLOW_STATE_PATH.exists():
            print("ERROR: No saved flow state. Run without arguments first to generate auth URL.")
            sys.exit(1)

        flow_state = json.loads(FLOW_STATE_PATH.read_text())

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_PATH), SCOPES
        )
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        flow.code_verifier = flow_state.get('code_verifier')

        flow.fetch_token(code=code)

        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(flow.credentials.to_json())

        # Clean up flow state
        FLOW_STATE_PATH.unlink(missing_ok=True)

        print(f"\nSuccess! Token saved to {TOKEN_PATH}")
        print("The ad sheet updater will now use this token automatically.")


if __name__ == '__main__':
    main()
