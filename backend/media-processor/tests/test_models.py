import pytest
from media_processor.models import (
    FileInput,
    FileType,
    SourceResult,
    ProcessingResult,
)


class TestFileInput:
    def test_file_input_creation(self):
        file_input = FileInput(
            data="YmFzZTY0ZGF0YQ==",
            type=FileType.IMAGE,
            filename="test.jpg",
        )
        assert file_input.data == "YmFzZTY0ZGF0YQ=="
        assert file_input.type == FileType.IMAGE
        assert file_input.filename == "test.jpg"

    def test_file_type_enum_values(self):
        assert FileType.IMAGE.value == "image"
        assert FileType.VIDEO.value == "video"
        assert FileType.AUDIO.value == "audio"
        assert FileType.PDF.value == "pdf"
        assert FileType.DOCX.value == "docx"


class TestSourceResult:
    def test_successful_result(self):
        result = SourceResult(
            filename="test.pdf",
            source_type="pdf",
            text_content="Extracted text with [PDF_1_IMAGE_1] placeholder",
            images={"PDF_1_IMAGE_1": "base64data"},
            processing_notes="Extracted 1 embedded image",
        )
        assert result.filename == "test.pdf"
        assert result.error is None

    def test_failed_result(self):
        result = SourceResult(
            filename="bad.pdf",
            source_type="pdf",
            error="Failed to parse PDF: file corrupted",
            text_content=None,
            images={},
        )
        assert result.error == "Failed to parse PDF: file corrupted"
        assert result.text_content is None


class TestProcessingResult:
    def test_processing_result_aggregation(self):
        sources = [
            SourceResult(
                filename="doc.pdf",
                source_type="pdf",
                text_content="text",
                images={},
            ),
            SourceResult(
                filename="bad.docx",
                source_type="docx",
                error="Corrupted",
                text_content=None,
                images={},
            ),
        ]
        result = ProcessingResult(sources=sources)
        assert result.processing_summary.total_files == 2
        assert result.processing_summary.successful == 1
        assert result.processing_summary.failed == 1
