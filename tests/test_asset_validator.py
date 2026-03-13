"""
Tests for AssetValidator.

Uses unittest.mock to avoid real file I/O and PIL dependencies.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from src.assets.validator import AssetValidator, ValidationError


def make_mock_path(exists=True, size_bytes=1024 * 1024, suffix=".jpg"):
    """Create a mock Path object."""
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = exists
    mock_stat = MagicMock()
    mock_stat.st_size = size_bytes
    mock_path.stat.return_value = mock_stat
    mock_path.suffix = suffix
    return mock_path


def make_mock_image(format="JPEG", width=1200, height=1200):
    """Create a mock PIL Image."""
    mock_img = MagicMock()
    mock_img.format = format
    mock_img.size = (width, height)
    mock_img.__enter__ = lambda s: s
    mock_img.__exit__ = MagicMock(return_value=False)
    return mock_img


class TestValidateImage:

    def test_valid_jpeg_returns_valid(self):
        path = make_mock_path(size_bytes=5 * 1024 * 1024)  # 5 MB
        mock_img = make_mock_image(format="JPEG", width=1200, height=1200)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_png_returns_valid(self):
        path = make_mock_path(size_bytes=2 * 1024 * 1024)
        mock_img = make_mock_image(format="PNG", width=1080, height=1080)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert result["valid"] is True

    def test_file_not_found_raises(self):
        path = make_mock_path(exists=False)
        with pytest.raises(ValidationError, match="File not found"):
            AssetValidator.validate_image(path)

    def test_oversized_image_is_invalid(self):
        # 31 MB — over the 30 MB limit
        path = make_mock_path(size_bytes=31 * 1024 * 1024)
        mock_img = make_mock_image(format="JPEG", width=1200, height=1200)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert result["valid"] is False
        assert any("exceeds maximum" in e for e in result["errors"])

    def test_unsupported_format_is_invalid(self):
        path = make_mock_path(size_bytes=1 * 1024 * 1024)
        mock_img = make_mock_image(format="BMP", width=1200, height=1200)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert result["valid"] is False
        assert any("Unsupported format" in e for e in result["errors"])

    def test_small_width_produces_warning(self):
        path = make_mock_path(size_bytes=1 * 1024 * 1024)
        mock_img = make_mock_image(format="JPEG", width=400, height=1200)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert any("Width" in w and "below recommended" in w for w in result["warnings"])

    def test_small_height_produces_warning(self):
        path = make_mock_path(size_bytes=1 * 1024 * 1024)
        mock_img = make_mock_image(format="JPEG", width=1200, height=400)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert any("Height" in w and "below recommended" in w for w in result["warnings"])

    def test_unusual_aspect_ratio_produces_warning(self):
        path = make_mock_path(size_bytes=1 * 1024 * 1024)
        # 3:1 ratio — not in RECOMMENDED_ASPECT_RATIOS
        mock_img = make_mock_image(format="JPEG", width=1800, height=600)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert any("aspect ratio" in w.lower() for w in result["warnings"])

    def test_square_aspect_ratio_no_warning(self):
        path = make_mock_path(size_bytes=1 * 1024 * 1024)
        mock_img = make_mock_image(format="JPEG", width=1080, height=1080)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        # No aspect ratio warning
        assert not any("aspect ratio" in w.lower() for w in result["warnings"])

    def test_metadata_populated(self):
        path = make_mock_path(size_bytes=2 * 1024 * 1024)
        mock_img = make_mock_image(format="JPEG", width=1200, height=1200)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_image(path)

        assert result["metadata"]["width"] == 1200
        assert result["metadata"]["height"] == 1200
        assert result["metadata"]["format"] == "JPEG"
        assert "size_mb" in result["metadata"]


class TestValidateVideo:

    def test_valid_mp4_returns_valid(self):
        path = make_mock_path(size_bytes=100 * 1024 * 1024, suffix=".mp4")
        result = AssetValidator.validate_video(path)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_mov_returns_valid(self):
        path = make_mock_path(size_bytes=50 * 1024 * 1024, suffix=".mov")
        result = AssetValidator.validate_video(path)
        assert result["valid"] is True

    def test_unsupported_extension_is_invalid(self):
        path = make_mock_path(size_bytes=10 * 1024 * 1024, suffix=".wmv")
        result = AssetValidator.validate_video(path)
        assert result["valid"] is False
        assert any("Unsupported video format" in e for e in result["errors"])

    def test_oversized_video_is_invalid(self):
        # 5 GB — over the 4 GB limit
        path = make_mock_path(size_bytes=5 * 1024 * 1024 * 1024, suffix=".mp4")
        result = AssetValidator.validate_video(path)
        assert result["valid"] is False
        assert any("exceeds maximum" in e for e in result["errors"])

    def test_file_not_found_raises(self):
        path = make_mock_path(exists=False, suffix=".mp4")
        with pytest.raises(ValidationError, match="File not found"):
            AssetValidator.validate_video(path)


class TestValidateFile:

    def test_image_mime_type_routes_to_validate_image(self):
        path = make_mock_path(size_bytes=1 * 1024 * 1024)
        mock_img = make_mock_image(format="JPEG", width=1200, height=1200)

        with patch("PIL.Image.open", return_value=mock_img):
            result = AssetValidator.validate_file(path, mime_type="image/jpeg")

        assert "width" in result["metadata"]

    def test_video_mime_type_routes_to_validate_video(self):
        path = make_mock_path(size_bytes=50 * 1024 * 1024, suffix=".mp4")
        result = AssetValidator.validate_file(path, mime_type="video/mp4")
        assert "extension" in result["metadata"]

    def test_no_mime_type_uses_extension(self):
        path = make_mock_path(size_bytes=50 * 1024 * 1024, suffix=".mp4")
        result = AssetValidator.validate_file(path, mime_type=None)
        assert "extension" in result["metadata"]


class TestGetRecommendations:

    def test_all_good_returns_checkmark(self):
        result = {"valid": True, "errors": [], "warnings": []}
        rec = AssetValidator.get_recommendations(result)
        assert "✅" in rec

    def test_errors_shown(self):
        result = {"valid": False, "errors": ["Too big"], "warnings": []}
        rec = AssetValidator.get_recommendations(result)
        assert "Too big" in rec
        assert "❌" in rec

    def test_warnings_shown(self):
        result = {"valid": True, "errors": [], "warnings": ["Small width"]}
        rec = AssetValidator.get_recommendations(result)
        assert "Small width" in rec
        assert "⚠️" in rec
