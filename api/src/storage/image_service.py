"""
Generic image processing service.
Handles image validation, resizing, format conversion, and compression.
"""

from io import BytesIO
from typing import Any, Dict, Tuple

from PIL import Image


class ImageProcessingError(Exception):
    """Raised when image processing fails."""

    pass


class ImageService:
    """
    Generic image processing service.
    No domain knowledge - categories are just strings for organization.
    """

    DEFAULT_MAX_WIDTH = 1200
    DEFAULT_MAX_SIZE = 10_000_000  # 10MB

    SUPPORTED_FORMATS = {"PNG", "JPEG", "JPG", "GIF", "WEBP", "BMP"}

    def process_image(
        self, file_data: bytes, max_width: int = DEFAULT_MAX_WIDTH, max_size: int = DEFAULT_MAX_SIZE, quality: int = 85
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Process image and return (image_data, metadata).

        Steps:
        - Validates format using PIL
        - Resizes to max_width (maintains aspect ratio)
        - Converts to WEBP with specified quality
        - Validates final size

        Args:
            file_data: Raw image bytes
            max_width: Maximum width in pixels (default 1200)
            max_size: Maximum file size in bytes (default 10MB)
            quality: WEBP compression quality 0-100 (default 85)

        Returns:
            Tuple of (binary_data, metadata_dict)
            metadata contains: {width, height, type, size}

        Raises:
            ImageProcessingError: If image is invalid or processing fails
        """
        # Validate input size
        if len(file_data) > max_size:
            raise ImageProcessingError(f"Image size {len(file_data)} bytes exceeds maximum {max_size} bytes")

        try:
            # Open and validate image
            img = Image.open(BytesIO(file_data))
            img.verify()  # Verify it's a valid image

            # Re-open after verify (verify closes the file)
            img = Image.open(BytesIO(file_data))

            # Check format is supported
            if img.format not in self.SUPPORTED_FORMATS:
                raise ImageProcessingError(
                    f"Unsupported image format: {img.format}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
                )

            # Convert to RGB if necessary (WEBP doesn't support all modes)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            # Resize if needed (maintaining aspect ratio)
            original_width, original_height = img.size
            if original_width > max_width:
                # Calculate new height maintaining aspect ratio
                ratio = max_width / original_width
                new_height = int(original_height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Convert to WEBP
            output = BytesIO()
            img.save(output, format="WEBP", quality=quality, method=6)
            processed_data = output.getvalue()

            # Validate processed size
            if len(processed_data) > max_size:
                raise ImageProcessingError(
                    f"Processed image size {len(processed_data)} bytes exceeds maximum {max_size} bytes"
                )

            # Get final dimensions
            final_width, final_height = img.size

            metadata = {"width": final_width, "height": final_height, "type": "image/webp", "size": len(processed_data)}

            return processed_data, metadata

        except ImageProcessingError:
            raise
        except Exception as e:
            raise ImageProcessingError(f"Failed to process image: {str(e)}")
