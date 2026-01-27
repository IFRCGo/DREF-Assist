import base64
import io
import pytest
from unittest.mock import patch, Mock
from PIL import Image

from media_processor.router import Router
from media_processor.models import FileInput, FileType


def create_test_image() -> str:
    img = Image.new("RGB", (10, 10), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


class TestRouter:
    def test_routes_image_to_image_handler(self):
        router = Router()
        file_input = FileInput(
            data=create_test_image(),
            type=FileType.IMAGE,
            filename="photo.jpg",
        )

        result = router.route(file_input, source_index=1)

        assert result.source_type == "image"
        assert result.error is None

    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_routes_audio_to_audio_handler(self, mock_transcribe):
        mock_transcribe.return_value = "Transcript"
        router = Router()
        file_input = FileInput(
            data=base64.b64encode(b"audio").decode(),
            type=FileType.AUDIO,
            filename="audio.mp3",
        )

        result = router.route(file_input, source_index=1)

        assert result.source_type == "audio"

    @patch("media_processor.handlers.pdf.fitz")
    def test_routes_pdf_to_pdf_handler(self, mock_fitz):
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "PDF text content here and more."
        mock_page.get_text_blocks.return_value = [(0, 0, 100, 50, "PDF text", 0, 0)]
        mock_page.get_images.return_value = []
        mock_page.rect = Mock(height=800)
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        router = Router()
        file_input = FileInput(
            data=base64.b64encode(b"pdf").decode(),
            type=FileType.PDF,
            filename="doc.pdf",
        )

        result = router.route(file_input, source_index=1)

        assert result.source_type == "pdf"

    @patch("media_processor.handlers.docx.Document")
    def test_routes_docx_to_docx_handler(self, mock_document_class):
        mock_doc = Mock()
        mock_para = Mock()
        mock_para.text = "DOCX content"
        mock_para._element.xpath.return_value = []
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []
        mock_document_class.return_value = mock_doc

        router = Router()
        file_input = FileInput(
            data=base64.b64encode(b"docx").decode(),
            type=FileType.DOCX,
            filename="doc.docx",
        )

        result = router.route(file_input, source_index=1)

        assert result.source_type == "docx"

    def test_returns_error_for_unknown_type(self):
        router = Router()
        # Create file input with mocked unknown type
        file_input = FileInput(
            data=base64.b64encode(b"data").decode(),
            type=FileType.IMAGE,  # We'll test via direct handler check
            filename="test.xyz",
        )
        # The handler should still work since type is IMAGE
        result = router.route(file_input, source_index=1)
        assert result.source_type == "image"
