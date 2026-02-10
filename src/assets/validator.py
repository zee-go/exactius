"""
Asset validation for Meta ads compliance.

Validates image and video assets against Meta's specifications:
- File formats
- File sizes
- Dimensions
- Aspect ratios
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class AssetValidator:
    """Validates assets for Meta ads compliance."""

    # Meta Ads specifications
    MAX_IMAGE_SIZE_MB = 30
    MAX_VIDEO_SIZE_MB = 4096  # 4 GB

    # Supported formats
    SUPPORTED_IMAGE_FORMATS = {'JPEG', 'JPG', 'PNG', 'GIF'}
    SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi'}

    # Recommended aspect ratios for Meta ads
    RECOMMENDED_ASPECT_RATIOS = {
        'square': (1, 1),
        'landscape': (16, 9),
        'vertical': (9, 16),
        'portrait': (4, 5),
    }

    # Minimum dimensions
    MIN_IMAGE_WIDTH = 600
    MIN_IMAGE_HEIGHT = 600

    @staticmethod
    def validate_image(file_path: Path) -> Dict[str, Any]:
        """
        Validate image file for Meta ads.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with validation results and metadata:
                - valid: bool
                - errors: List[str]
                - warnings: List[str]
                - metadata: Dict (width, height, format, size, aspect_ratio)

        Raises:
            ValidationError: If file cannot be opened or is corrupt
        """
        errors = []
        warnings = []
        metadata = {}

        try:
            # Check file exists
            if not file_path.exists():
                raise ValidationError(f"File not found: {file_path}")

            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            metadata['size_mb'] = round(file_size_mb, 2)

            if file_size_mb > AssetValidator.MAX_IMAGE_SIZE_MB:
                errors.append(
                    f"File size ({file_size_mb:.2f} MB) exceeds maximum "
                    f"({AssetValidator.MAX_IMAGE_SIZE_MB} MB)"
                )

            # Open and validate image
            try:
                with Image.open(file_path) as img:
                    # Get format
                    img_format = img.format
                    metadata['format'] = img_format

                    # Check format
                    if img_format not in AssetValidator.SUPPORTED_IMAGE_FORMATS:
                        errors.append(
                            f"Unsupported format: {img_format}. "
                            f"Supported: {', '.join(AssetValidator.SUPPORTED_IMAGE_FORMATS)}"
                        )

                    # Get dimensions
                    width, height = img.size
                    metadata['width'] = width
                    metadata['height'] = height

                    # Check minimum dimensions
                    if width < AssetValidator.MIN_IMAGE_WIDTH:
                        warnings.append(
                            f"Width ({width}px) below recommended minimum "
                            f"({AssetValidator.MIN_IMAGE_WIDTH}px)"
                        )

                    if height < AssetValidator.MIN_IMAGE_HEIGHT:
                        warnings.append(
                            f"Height ({height}px) below recommended minimum "
                            f"({AssetValidator.MIN_IMAGE_HEIGHT}px)"
                        )

                    # Calculate aspect ratio
                    aspect_ratio = width / height
                    metadata['aspect_ratio'] = round(aspect_ratio, 2)

                    # Check aspect ratio
                    aspect_ratio_name = AssetValidator._get_aspect_ratio_name(
                        width, height
                    )
                    metadata['aspect_ratio_name'] = aspect_ratio_name

                    if not aspect_ratio_name:
                        warnings.append(
                            f"Unusual aspect ratio: {aspect_ratio:.2f}. "
                            "May not display optimally on all placements."
                        )

            except Exception as e:
                raise ValidationError(f"Failed to open image: {str(e)}")

            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Validation error for {file_path}: {str(e)}")
            raise

    @staticmethod
    def validate_video(file_path: Path) -> Dict[str, Any]:
        """
        Validate video file for Meta ads.

        Args:
            file_path: Path to video file

        Returns:
            Dictionary with validation results and metadata

        Raises:
            ValidationError: If file cannot be validated
        """
        errors = []
        warnings = []
        metadata = {}

        try:
            # Check file exists
            if not file_path.exists():
                raise ValidationError(f"File not found: {file_path}")

            # Check file extension
            extension = file_path.suffix.lower()
            metadata['extension'] = extension

            if extension not in AssetValidator.SUPPORTED_VIDEO_EXTENSIONS:
                errors.append(
                    f"Unsupported video format: {extension}. "
                    f"Supported: {', '.join(AssetValidator.SUPPORTED_VIDEO_EXTENSIONS)}"
                )

            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            metadata['size_mb'] = round(file_size_mb, 2)

            if file_size_mb > AssetValidator.MAX_VIDEO_SIZE_MB:
                errors.append(
                    f"File size ({file_size_mb:.2f} MB) exceeds maximum "
                    f"({AssetValidator.MAX_VIDEO_SIZE_MB} MB)"
                )

            # Note: Full video validation (codec, duration, etc.) would require
            # ffmpeg/moviepy, which we're not including in initial implementation.
            # Meta will validate these on upload.

            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Validation error for {file_path}: {str(e)}")
            raise

    @staticmethod
    def validate_file(file_path: Path, mime_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate file based on type (auto-detect or use mime_type).

        Args:
            file_path: Path to file
            mime_type: Optional MIME type (will auto-detect if not provided)

        Returns:
            Validation results dictionary

        Raises:
            ValidationError: If validation fails
        """
        if mime_type and mime_type.startswith('video/'):
            return AssetValidator.validate_video(file_path)
        elif mime_type and mime_type.startswith('image/'):
            return AssetValidator.validate_image(file_path)
        else:
            # Auto-detect based on extension
            extension = file_path.suffix.lower()
            if extension in AssetValidator.SUPPORTED_VIDEO_EXTENSIONS:
                return AssetValidator.validate_video(file_path)
            else:
                return AssetValidator.validate_image(file_path)

    @staticmethod
    def _get_aspect_ratio_name(width: int, height: int) -> Optional[str]:
        """
        Get aspect ratio name if matches a known ratio.

        Args:
            width: Image width
            height: Image height

        Returns:
            Aspect ratio name or None if no match
        """
        ratio = width / height
        tolerance = 0.05  # 5% tolerance

        for name, (w_ratio, h_ratio) in AssetValidator.RECOMMENDED_ASPECT_RATIOS.items():
            expected_ratio = w_ratio / h_ratio
            if abs(ratio - expected_ratio) / expected_ratio <= tolerance:
                return name

        return None

    @staticmethod
    def get_recommendations(validation_result: Dict[str, Any]) -> str:
        """
        Get human-readable recommendations based on validation results.

        Args:
            validation_result: Result from validate_image/validate_video

        Returns:
            Formatted recommendations string
        """
        if validation_result['valid'] and not validation_result['warnings']:
            return "✅ Asset meets all Meta ads specifications."

        output = []

        if validation_result['errors']:
            output.append("❌ Errors (must fix):")
            for error in validation_result['errors']:
                output.append(f"  - {error}")

        if validation_result['warnings']:
            output.append("\n⚠️  Warnings (recommended to fix):")
            for warning in validation_result['warnings']:
                output.append(f"  - {warning}")

        return "\n".join(output)
