"""
Tests for DriveURLParser.
"""

import pytest
from src.drive.parser import DriveURLParser


FOLDER_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"
FILE_ID = "1DrGuvWcVDNw2GEBqFpMN6U9yRBOhJoAq"


class TestParseFolderURLs:

    @pytest.mark.parametrize("url", [
        f"https://drive.google.com/drive/folders/{FOLDER_ID}",
        f"https://drive.google.com/drive/folders/{FOLDER_ID}/",
        f"https://drive.google.com/drive/u/0/folders/{FOLDER_ID}",
        f"https://drive.google.com/drive/u/1/folders/{FOLDER_ID}",
    ])
    def test_folder_urls(self, url):
        resource_type, resource_id = DriveURLParser.parse(url)
        assert resource_type == "folder"
        assert resource_id == FOLDER_ID

    def test_open_url_treated_as_folder(self):
        url = f"https://drive.google.com/open?id={FOLDER_ID}"
        resource_type, resource_id = DriveURLParser.parse(url)
        assert resource_type == "folder"
        assert resource_id == FOLDER_ID

    def test_query_param_url(self):
        url = f"https://drive.google.com/drive?id={FOLDER_ID}"
        resource_type, resource_id = DriveURLParser.parse(url)
        assert resource_type == "folder"
        assert resource_id == FOLDER_ID


class TestParseFileURLs:

    @pytest.mark.parametrize("url", [
        f"https://drive.google.com/file/d/{FILE_ID}/view",
        f"https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing",
        f"https://drive.google.com/file/d/{FILE_ID}",
    ])
    def test_file_urls(self, url):
        resource_type, resource_id = DriveURLParser.parse(url)
        assert resource_type == "file"
        assert resource_id == FILE_ID


class TestParseInvalidURLs:

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            DriveURLParser.parse("")

    def test_none_raises(self):
        with pytest.raises((ValueError, AttributeError, TypeError)):
            DriveURLParser.parse(None)

    def test_wrong_domain_raises(self):
        with pytest.raises(ValueError, match="drive.google.com"):
            DriveURLParser.parse("https://docs.google.com/folder/abc123")

    def test_drive_url_no_id_raises(self):
        with pytest.raises(ValueError):
            DriveURLParser.parse("https://drive.google.com/drive/")

    def test_not_a_url_raises(self):
        with pytest.raises(ValueError):
            DriveURLParser.parse("not-a-url")


class TestExtractHelpers:

    def test_extract_id_folder(self):
        url = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
        assert DriveURLParser.extract_id(url) == FOLDER_ID

    def test_extract_id_file(self):
        url = f"https://drive.google.com/file/d/{FILE_ID}/view"
        assert DriveURLParser.extract_id(url) == FILE_ID

    def test_extract_folder_id_success(self):
        url = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
        assert DriveURLParser.extract_folder_id(url) == FOLDER_ID

    def test_extract_folder_id_from_file_raises(self):
        url = f"https://drive.google.com/file/d/{FILE_ID}/view"
        with pytest.raises(ValueError, match="not a folder"):
            DriveURLParser.extract_folder_id(url)

    def test_extract_file_id_success(self):
        url = f"https://drive.google.com/file/d/{FILE_ID}/view"
        assert DriveURLParser.extract_file_id(url) == FILE_ID

    def test_extract_file_id_from_folder_raises(self):
        url = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
        with pytest.raises(ValueError, match="not a file"):
            DriveURLParser.extract_file_id(url)


class TestIsValidDriveURL:

    def test_valid_folder_url(self):
        assert DriveURLParser.is_valid_drive_url(
            f"https://drive.google.com/drive/folders/{FOLDER_ID}"
        ) is True

    def test_valid_file_url(self):
        assert DriveURLParser.is_valid_drive_url(
            f"https://drive.google.com/file/d/{FILE_ID}/view"
        ) is True

    def test_invalid_url_returns_false(self):
        assert DriveURLParser.is_valid_drive_url("https://dropbox.com/foo") is False

    def test_empty_returns_false(self):
        assert DriveURLParser.is_valid_drive_url("") is False

    def test_none_returns_false(self):
        assert DriveURLParser.is_valid_drive_url(None) is False
