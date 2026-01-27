"""Integration tests for end-to-end media processing."""
import base64
import io
import pytest
from unittest.mock import patch, Mock, MagicMock
from PIL import Image

from media_processor import MediaProcessor, format_for_llm
from media_processor.models import ProcessingInput, FileInput, FileType


def create_test_image(format: str = "JPEG") -> str:
    img = Image.new("RGB", (100, 100), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode()


class TestEndToEndProcessing:
    def test_image_through_to_llm_format(self):
        """Test full pipeline: image file -> processor -> LLM format."""
        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(
                data=create_test_image(),
                type=FileType.IMAGE,
                filename="damage_photo.jpg",
            )
        ])

        result = processor.process(input_data)
        llm_message = format_for_llm(result, user_message="Assess the damage in this photo")

        # Verify structure
        assert llm_message["role"] == "user"
        assert len(llm_message["content"]) == 2  # text + image

        # Text should have source header
        text_block = llm_message["content"][0]
        assert "damage_photo.jpg" in text_block["text"]

        # Image should be base64 URL
        image_block = llm_message["content"][1]
        assert image_block["image_url"]["url"].startswith("data:image/")

    @patch("media_processor.handlers.pdf.fitz")
    def test_pdf_with_images_through_to_llm_format(self, mock_fitz):
        """Test PDF with embedded images through full pipeline."""
        # Setup mock PDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect = MagicMock(height=800)

        # Text content - needs enough to pass scanned detection (100 chars/page)
        text_before = "Flooding observed in district. " * 5
        text_after = "Water level reached 1.2 meters. " * 5

        # get_text() is called to check for scanned documents - must return string
        mock_page.get_text.return_value = text_before + text_after
        mock_page.get_text_blocks.return_value = [
            (0, 0, 100, 50, text_before, 0, 0),
            (0, 150, 100, 200, text_after, 0, 0),
        ]
        mock_page.get_images.return_value = [(1, 0, 100, 100, 8, "cs", "", "Im0", "")]
        mock_page.get_image_rects.return_value = [MagicMock(y0=100)]

        img = Image.new("RGB", (50, 50), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        mock_doc.extract_image.return_value = {
            "image": buffer.getvalue(),
            "ext": "png",
        }

        # Return a fresh iterator each time __iter__ is called (document is iterated twice)
        mock_doc.__iter__ = Mock(side_effect=lambda: iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(
                data=base64.b64encode(b"pdf data").decode(),
                type=FileType.PDF,
                filename="situation_report.pdf",
            )
        ])

        result = processor.process(input_data)
        llm_message = format_for_llm(result, user_message="Summarize this situation report")

        # Verify text contains placeholder
        text = llm_message["content"][0]["text"]
        assert "[PDF_1_IMAGE_" in text
        assert "Flooding" in text

        # Verify image is included
        assert len(llm_message["content"]) >= 2
        assert any(c["type"] == "image_url" for c in llm_message["content"])

    def test_mixed_success_and_failure(self):
        """Test that failures don't affect successful files in LLM output."""
        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(
                data=create_test_image(),
                type=FileType.IMAGE,
                filename="good.jpg",
            ),
            FileInput(
                data=base64.b64encode(b"not an image").decode(),
                type=FileType.IMAGE,
                filename="bad.jpg",
            ),
        ])

        result = processor.process(input_data)
        llm_message = format_for_llm(result, user_message="Analyze these")

        # Good file should be in output
        text = llm_message["content"][0]["text"]
        assert "good.jpg" in text

        # Bad file should NOT be in output
        assert "bad.jpg" not in text

        # Should still have the good image
        assert len(llm_message["content"]) == 2

    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_audio_produces_transcript_only(self, mock_transcribe):
        """Test that audio files produce text without images."""
        mock_transcribe.return_value = "Field assessment notes: Heavy rainfall expected."

        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(
                data=base64.b64encode(b"audio").decode(),
                type=FileType.AUDIO,
                filename="field_notes.mp3",
            )
        ])

        result = processor.process(input_data)
        llm_message = format_for_llm(result, user_message="What was recorded?")

        # Only text, no images
        assert len(llm_message["content"]) == 1
        assert llm_message["content"][0]["type"] == "text"
        assert "Heavy rainfall" in llm_message["content"][0]["text"]
