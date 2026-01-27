import base64
import io
import pytest
from unittest.mock import patch, Mock, MagicMock

from media_processor.handlers.pdf import PDFHandler
from media_processor.models import FileInput, FileType


class TestPDFHandler:
    @patch("media_processor.handlers.pdf.fitz")
    def test_process_text_only_pdf(self, mock_fitz):
        # Mock a simple PDF with just text
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # Need enough text to pass scanned document detection (100 chars/page)
        long_text = "This is the extracted PDF text content. " * 10
        mock_page.get_text.return_value = long_text
        mock_page.get_images.return_value = []
        mock_page.rect = MagicMock(height=800)

        # Mock text blocks with positions
        mock_page.get_text_blocks.return_value = [
            (0, 0, 100, 50, long_text, 0, 0),
        ]

        # Return a fresh iterator each time __iter__ is called
        mock_doc.__iter__ = Mock(side_effect=lambda: iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        handler = PDFHandler()
        data = base64.b64encode(b"fake pdf data").decode()
        file_input = FileInput(data=data, type=FileType.PDF, filename="test.pdf")

        result = handler.process(file_input, source_index=1)

        assert result.filename == "test.pdf"
        assert result.source_type == "pdf"
        assert "extracted" in result.text_content.lower() or len(result.text_content) > 0
        assert result.error is None

    @patch("media_processor.handlers.pdf.fitz")
    def test_process_pdf_with_images(self, mock_fitz):
        # Mock PDF with text and embedded images
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect = MagicMock(height=800)

        # Text blocks - need enough text to pass scanned detection
        long_text_before = "Text before image. " * 10
        long_text_after = "Text after image. " * 10
        mock_page.get_text_blocks.return_value = [
            (0, 0, 100, 50, long_text_before, 0, 0),
            (0, 200, 100, 250, long_text_after, 0, 0),
        ]

        # Image with position between text blocks
        mock_page.get_images.return_value = [(0, 0, 100, 100, 8, "cs", "", "Im0", "")]
        mock_page.get_image_rects.return_value = [MagicMock(y0=100)]  # Between texts

        # Mock image extraction
        mock_doc.extract_image.return_value = {
            "image": b"fake image bytes",
            "ext": "png",
        }

        # Return a fresh iterator each time __iter__ is called
        mock_doc.__iter__ = Mock(side_effect=lambda: iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        # Mock get_text to return enough chars to not trigger scanned detection
        mock_page.get_text.return_value = long_text_before + long_text_after

        handler = PDFHandler()
        data = base64.b64encode(b"fake pdf").decode()
        file_input = FileInput(data=data, type=FileType.PDF, filename="report.pdf")

        result = handler.process(file_input, source_index=1)

        assert result.error is None
        assert len(result.images) > 0
        # Should have placeholder in text
        assert "[PDF_1_IMAGE_" in result.text_content

    def test_reject_oversized_pdf(self):
        handler = PDFHandler()
        large_data = base64.b64encode(b"x" * (51 * 1024 * 1024)).decode()
        file_input = FileInput(data=large_data, type=FileType.PDF, filename="huge.pdf")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "50MB" in result.error

    @patch("media_processor.handlers.pdf.fitz")
    def test_reject_too_many_pages(self, mock_fitz):
        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=51)  # Over 50 page limit
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        handler = PDFHandler()
        data = base64.b64encode(b"pdf data").decode()
        file_input = FileInput(data=data, type=FileType.PDF, filename="long.pdf")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "50" in result.error and "page" in result.error.lower()

    @patch("media_processor.handlers.pdf.fitz")
    def test_fallback_to_page_rendering_for_scanned_pdf(self, mock_fitz):
        # Mock a scanned PDF with very little text
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "ab"  # Less than 100 chars
        mock_page.get_text_blocks.return_value = [(0, 0, 10, 10, "ab", 0, 0)]
        mock_page.get_images.return_value = []
        mock_page.rect = MagicMock(height=800, width=600)

        # Mock page rendering
        mock_pixmap = MagicMock()
        mock_pixmap.tobytes.return_value = b"rendered page image"
        mock_page.get_pixmap.return_value = mock_pixmap

        # Return a fresh iterator each time __iter__ is called
        mock_doc.__iter__ = Mock(side_effect=lambda: iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        # Mock the Matrix class
        mock_fitz.Matrix.return_value = MagicMock()

        handler = PDFHandler()
        data = base64.b64encode(b"scanned pdf").decode()
        file_input = FileInput(data=data, type=FileType.PDF, filename="scanned.pdf")

        result = handler.process(file_input, source_index=1)

        assert result.error is None
        # Should have rendered page as image
        assert len(result.images) > 0
        assert "scanned" in result.processing_notes.lower() or "render" in result.processing_notes.lower()

    @patch("media_processor.handlers.pdf.fitz")
    def test_corrupted_pdf_returns_error(self, mock_fitz):
        mock_fitz.open.side_effect = Exception("Cannot open PDF")

        handler = PDFHandler()
        data = base64.b64encode(b"corrupted").decode()
        file_input = FileInput(data=data, type=FileType.PDF, filename="bad.pdf")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "corrupted" in result.error.lower() or "failed" in result.error.lower()
