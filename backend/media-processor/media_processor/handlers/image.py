"""Image file handler - validation and passthrough."""
import base64
import io
from PIL import Image

from media_processor.models import FileInput, SourceResult


class ImageHandler:
    """Handler for image files (JPEG, PNG, WebP, GIF)."""

    SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
    MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20MB

    def process(self, file_input: FileInput, source_index: int) -> SourceResult:
        """Process an image file.

        Args:
            file_input: The file input containing base64 data
            source_index: Index for namespacing (IMAGE_N)

        Returns:
            SourceResult with the image or error
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(file_input.data)

            # Check size limit
            if len(image_bytes) > self.MAX_SIZE_BYTES:
                return SourceResult(
                    filename=file_input.filename,
                    source_type="image",
                    error=f"File exceeds size limit of 20MB",
                    images={},
                )

            # Validate image format
            try:
                img = Image.open(io.BytesIO(image_bytes))
                img_format = img.format
            except Exception:
                return SourceResult(
                    filename=file_input.filename,
                    source_type="image",
                    error="Failed to parse image: file corrupted or invalid",
                    images={},
                )

            if img_format not in self.SUPPORTED_FORMATS:
                return SourceResult(
                    filename=file_input.filename,
                    source_type="image",
                    error=f"Unsupported image format '{img_format}'. Supported: JPEG, PNG, WebP, GIF",
                    images={},
                )

            # Pass through as-is
            image_key = f"IMAGE_{source_index}"
            return SourceResult(
                filename=file_input.filename,
                source_type="image",
                text_content=None,
                images={image_key: file_input.data},
            )

        except Exception as e:
            return SourceResult(
                filename=file_input.filename,
                source_type="image",
                error=f"Failed to process image: {str(e)}",
                images={},
            )
