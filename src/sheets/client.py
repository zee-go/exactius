"""
Google Sheets API client for reading and writing spreadsheet data.

Supports two authentication modes:
1. OAuth (local dev) — user logs in via browser once, token saved locally
2. Service account (production) — uses service account JSON from Secret Manager
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Default paths for OAuth token storage
DEFAULT_TOKEN_PATH = Path.home() / '.exactius' / 'sheets_token.json'
DEFAULT_CLIENT_SECRETS_PATH = Path.home() / '.exactius' / 'client_secret.json'


class SheetsClient:
    """Google Sheets API client with OAuth or service account authentication."""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, credentials):
        """
        Initialize Sheets client with pre-built credentials.

        Use the class methods from_oauth() or from_service_account() instead.

        Args:
            credentials: Google auth credentials object
        """
        self.credentials = credentials
        self.service = build('sheets', 'v4', credentials=self.credentials)
        logger.info("Initialized Sheets client")

    @classmethod
    def from_oauth(
        cls,
        client_secrets_path: Optional[str] = None,
        token_path: Optional[str] = None,
    ) -> 'SheetsClient':
        """
        Create a SheetsClient using OAuth (browser login).

        On first run, opens a browser for the user to authorize.
        Saves the token locally for future runs.

        Args:
            client_secrets_path: Path to OAuth client secrets JSON
            token_path: Path to save/load the OAuth token

        Returns:
            Authenticated SheetsClient
        """
        client_secrets = Path(client_secrets_path or DEFAULT_CLIENT_SECRETS_PATH)
        token_file = Path(token_path or DEFAULT_TOKEN_PATH)

        if not client_secrets.exists():
            raise ValueError(
                f"OAuth client secrets not found at {client_secrets}. "
                f"Download it from Google Cloud Console > APIs & Services > Credentials "
                f"and save it to {DEFAULT_CLIENT_SECRETS_PATH}"
            )

        credentials = None

        # Try to load existing token
        if token_file.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(token_file), cls.SCOPES
                )
            except Exception as e:
                logger.warning(f"Could not load saved token: {str(e)}")

        # Refresh or get new credentials
        if credentials and credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired OAuth token")
            credentials.refresh(Request())
        elif not credentials or not credentials.valid:
            logger.info("Starting OAuth flow — opening browser for authorization")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets), cls.SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save token for next time
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(credentials.to_json())
        logger.info(f"OAuth token saved to {token_file}")

        return cls(credentials)

    @classmethod
    def from_service_account(cls, service_account_json: str) -> 'SheetsClient':
        """
        Create a SheetsClient using a service account.

        Args:
            service_account_json: Service account credentials JSON string

        Returns:
            Authenticated SheetsClient
        """
        try:
            credentials_dict = json.loads(service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=cls.SCOPES
            )
            return cls(credentials)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid service account JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load service account credentials: {str(e)}")

    def get_sheet_values(
        self,
        spreadsheet_id: str,
        range_name: str
    ) -> List[List[str]]:
        """
        Read values from a sheet range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range (e.g., 'Sheet1!A:G')

        Returns:
            List of rows, each row is a list of cell values

        Raises:
            ValueError: If sheet not found or access denied
        """
        try:
            logger.debug(f"Reading values from {range_name}")

            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            rows = result.get('values', [])
            logger.info(f"Read {len(rows)} row(s) from {range_name}")
            return rows

        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(
                    f"Spreadsheet not found: {spreadsheet_id}. "
                    f"Check that the spreadsheet ID is correct."
                )
            elif e.resp.status == 403:
                raise ValueError(
                    f"Access denied to spreadsheet: {spreadsheet_id}. "
                    f"Make sure the sheet is shared with your account."
                )
            else:
                raise ValueError(f"Sheets API error: {str(e)}")

    def append_rows(
        self,
        spreadsheet_id: str,
        range_name: str,
        rows: List[List[str]]
    ) -> int:
        """
        Append rows to a sheet.

        Automatically finds the last row and appends below it.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range (e.g., 'Sheet1!A:G')
            rows: List of rows to append, each row is a list of cell values

        Returns:
            Number of rows appended

        Raises:
            ValueError: If sheet not found or access denied
        """
        if not rows:
            logger.info("No rows to append")
            return 0

        try:
            logger.info(f"Appending {len(rows)} row(s) to {range_name}")

            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': rows}
            ).execute()

            updates = result.get('updates', {})
            rows_appended = updates.get('updatedRows', len(rows))
            logger.info(f"Appended {rows_appended} row(s)")
            return rows_appended

        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(
                    f"Spreadsheet not found: {spreadsheet_id}. "
                    f"Check that the spreadsheet ID is correct."
                )
            elif e.resp.status == 403:
                raise ValueError(
                    f"Access denied to spreadsheet: {spreadsheet_id}. "
                    f"Make sure you have Editor access to the sheet."
                )
            else:
                raise ValueError(f"Sheets API error: {str(e)}")

    def ensure_header_row(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        headers: List[str]
    ) -> None:
        """
        Ensure the sheet has a header row. Adds one if the sheet is empty.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Sheet tab name
            headers: List of header column names
        """
        range_name = f'{sheet_name}!A1:1'
        existing = self.get_sheet_values(spreadsheet_id, range_name)

        if not existing:
            logger.info("Sheet is empty, adding header row")
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': [headers]}
            ).execute()
