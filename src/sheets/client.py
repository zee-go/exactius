"""
Google Sheets API client for reading and writing spreadsheet data.

Authenticates using service account credentials from Secret Manager
and provides methods for appending rows and reading sheet data.
"""

import json
import logging
from typing import List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class SheetsClient:
    """Google Sheets API client with service account authentication."""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, service_account_json: str):
        """
        Initialize Sheets client with service account.

        Args:
            service_account_json: Service account credentials JSON string
        """
        self.credentials = self._load_credentials(service_account_json)
        self.service = build('sheets', 'v4', credentials=self.credentials)
        logger.info("Initialized Sheets client with service account")

    def _load_credentials(self, credentials_json: str) -> service_account.Credentials:
        """
        Load service account credentials from JSON string.

        Args:
            credentials_json: Service account JSON as string

        Returns:
            Service account credentials with Sheets scope
        """
        try:
            credentials_dict = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=self.SCOPES
            )
            return credentials
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
                    f"Make sure the sheet is shared with the service account."
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
                    f"Make sure the sheet is shared with the service account as Editor."
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
