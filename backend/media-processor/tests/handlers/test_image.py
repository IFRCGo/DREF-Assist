import base64
import io
import pytest
from PIL import Image

from media_processor.handlers.image import ImageHandler
from media_processor.models import FileInput, FileType


def create_test_image(format: str = "JPEG", size: tuple = (100, 100)) -> str:
    """Create a base64-encoded test image."""
    img = Image.new("RGB", size, color="red")
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode()


class TestImageHandler:
    def test_process_valid_jpeg(self):
        handler = ImageHandler()
        data = create_test_image("JPEG")
        file_input = FileInput(data=data, type=FileType.IMAGE, filename="test.jpg")

        result = handler.process(file_input, source_index=1)

        assert result.filename == "test.jpg"
        assert result.source_type == "image"
        assert result.text_content is None
        assert "IMAGE_1" in result.images
        assert result.error is None

    def test_process_valid_png(self):
        handler = ImageHandler()
        data = create_test_image("PNG")
        file_input = FileInput(data=data, type=FileType.IMAGE, filename="test.png")

        result = handler.process(file_input, source_index=2)

        assert "IMAGE_2" in result.images
        assert result.error is None

    def test_process_valid_webp(self):
        handler = ImageHandler()
        data = create_test_image("WEBP")
        file_input = FileInput(data=data, type=FileType.IMAGE, filename="test.webp")

        result = handler.process(file_input, source_index=1)

        assert result.error is None

    def test_process_valid_gif(self):
        handler = ImageHandler()
        data = create_test_image("GIF")
        file_input = FileInput(data=data, type=FileType.IMAGE, filename="test.gif")

        result = handler.process(file_input, source_index=1)

        assert result.error is None

    def test_reject_unsupported_format(self):
        handler = ImageHandler()
        # Create a BMP image (unsupported)
        data = create_test_image("BMP")
        file_input = FileInput(data=data, type=FileType.IMAGE, filename="test.bmp")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "Unsupported" in result.error
        assert "JPEG, PNG, WebP, GIF" in result.error

    def test_reject_oversized_image(self):
        handler = ImageHandler()
        # Create data that claims to be >20MB
        large_data = base64.b64encode(b"x" * (21 * 1024 * 1024)).decode()
        file_input = FileInput(data=large_data, type=FileType.IMAGE, filename="huge.jpg")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "20MB" in result.error

    def test_reject_corrupted_image(self):
        handler = ImageHandler()
        bad_data = base64.b64encode(b"not an image").decode()
        file_input = FileInput(data=bad_data, type=FileType.IMAGE, filename="bad.jpg")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
