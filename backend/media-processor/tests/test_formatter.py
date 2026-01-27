import pytest

from media_processor.formatter import format_for_llm
from media_processor.models import ProcessingResult, SourceResult


class TestFormatForLLM:
    def test_text_only_source(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="doc.pdf",
                source_type="pdf",
                text_content="Extracted text from PDF.",
                images={},
            )
        ])

        llm_message = format_for_llm(result, user_message="Please analyze this")

        assert llm_message["role"] == "user"
        assert len(llm_message["content"]) == 1
        assert llm_message["content"][0]["type"] == "text"
        assert "Please analyze this" in llm_message["content"][0]["text"]
        assert "[SOURCE: doc.pdf]" in llm_message["content"][0]["text"]
        assert "Extracted text from PDF" in llm_message["content"][0]["text"]

    def test_image_only_source(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="photo.jpg",
                source_type="image",
                text_content=None,
                images={"IMAGE_1": "base64imagedata"},
            )
        ])

        llm_message = format_for_llm(result, user_message="What's in this image?")

        assert llm_message["role"] == "user"
        # Should have text + image
        assert len(llm_message["content"]) == 2

        text_block = llm_message["content"][0]
        assert text_block["type"] == "text"
        assert "What's in this image?" in text_block["text"]

        image_block = llm_message["content"][1]
        assert image_block["type"] == "image_url"
        assert "base64imagedata" in image_block["image_url"]["url"]

    def test_source_with_text_and_images(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="report.pdf",
                source_type="pdf",
                text_content="Flooding observed. [PDF_1_IMAGE_1] Water level high. [PDF_1_IMAGE_2] Evacuation needed.",
                images={
                    "PDF_1_IMAGE_1": "floodimage",
                    "PDF_1_IMAGE_2": "waterimage",
                },
            )
        ])

        llm_message = format_for_llm(result, user_message="Summarize this report")

        text_block = llm_message["content"][0]
        assert "[PDF_1_IMAGE_1]" in text_block["text"]
        assert "[PDF_1_IMAGE_2]" in text_block["text"]

        # Images should follow text in order
        assert len(llm_message["content"]) == 3  # 1 text + 2 images
        assert llm_message["content"][1]["type"] == "image_url"
        assert llm_message["content"][2]["type"] == "image_url"

    def test_multiple_sources(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="doc1.pdf",
                source_type="pdf",
                text_content="First document content.",
                images={},
            ),
            SourceResult(
                filename="doc2.docx",
                source_type="docx",
                text_content="Second document content.",
                images={},
            ),
        ])

        llm_message = format_for_llm(result, user_message="Compare these")

        text = llm_message["content"][0]["text"]
        assert "[SOURCE: doc1.pdf]" in text
        assert "[SOURCE: doc2.docx]" in text
        assert "First document" in text
        assert "Second document" in text
        # Sources should be separated
        assert "---" in text

    def test_images_ordered_by_placeholder_appearance(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="report.pdf",
                source_type="pdf",
                text_content="See [PDF_1_IMAGE_2] first, then [PDF_1_IMAGE_1].",
                images={
                    "PDF_1_IMAGE_1": "imageA",
                    "PDF_1_IMAGE_2": "imageB",
                },
            )
        ])

        llm_message = format_for_llm(result, user_message="Analyze")

        # Images should appear in order of placeholder occurrence
        # [PDF_1_IMAGE_2] appears first in text, so imageB should be first
        assert "imageB" in llm_message["content"][1]["image_url"]["url"]
        assert "imageA" in llm_message["content"][2]["image_url"]["url"]

    def test_failed_source_excluded_from_output(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="good.pdf",
                source_type="pdf",
                text_content="Good content.",
                images={},
            ),
            SourceResult(
                filename="bad.pdf",
                source_type="pdf",
                error="Failed to parse",
                text_content=None,
                images={},
            ),
        ])

        llm_message = format_for_llm(result, user_message="Review")

        text = llm_message["content"][0]["text"]
        assert "[SOURCE: good.pdf]" in text
        # Failed source should not appear in output
        assert "[SOURCE: bad.pdf]" not in text

    def test_image_url_format(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="photo.jpg",
                source_type="image",
                images={"IMAGE_1": "aGVsbG8="},  # base64 "hello"
            )
        ])

        llm_message = format_for_llm(result, user_message="")

        image_url = llm_message["content"][1]["image_url"]["url"]
        assert image_url.startswith("data:image/")
        assert ";base64," in image_url
        assert "aGVsbG8=" in image_url

    def test_empty_user_message(self):
        result = ProcessingResult(sources=[
            SourceResult(
                filename="doc.pdf",
                source_type="pdf",
                text_content="Content here.",
                images={},
            )
        ])

        llm_message = format_for_llm(result, user_message="")

        # Should still work with empty user message
        assert llm_message["role"] == "user"
        assert "Content here" in llm_message["content"][0]["text"]
