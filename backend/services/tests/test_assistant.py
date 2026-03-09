"""Tests for the assistant service module."""

import json
from unittest.mock import Mock, patch, MagicMock

from services.assistant import process_user_input


class TestProcessUserInput:
    """Tests for the main process_user_input function."""

    def _create_mock_client(self, response_content: str):
        """Helper to create a mock AzureOpenAI client."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()

        mock_message.content = response_content
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        return mock_client

    def test_text_only_message(self):
        """Test processing a simple text message without files."""
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I've noted the flood in Bangladesh.",
            "field_updates": [
                {"field_id": "operation_overview.disaster_type", "value": "Flood"},
            ]
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="There was a flood in Bangladesh",
            enriched_form_state={},
            client=mock_client,
        )

        assert result["classification"] == "NEW_INFORMATION"
        assert "Bangladesh" in result["reply"]
        assert len(result["field_updates"]) == 1
        assert "processing_summary" not in result
        assert "conflicts" in result

    def test_text_with_conversation_history(self):
        """Test that conversation history is passed through."""
        response = json.dumps({
            "classification": "MODIFICATION_REQUEST",
            "reply": "Updated to 7500.",
            "field_updates": [
                {"field_id": "event_detail.total_affected_population", "value": 7500},
            ]
        })
        mock_client = self._create_mock_client(response)

        history = [
            {"role": "user", "content": "5000 people were affected"},
            {"role": "assistant", "content": "I've recorded 5000 affected."},
        ]

        result = process_user_input(
            user_message="Actually it's 7500",
            enriched_form_state={
                "event_detail.total_affected_population": {
                    "value": 5000,
                    "source": "user_message",
                    "timestamp": "2024-01-01T00:00:00",
                }
            },
            conversation_history=history,
            client=mock_client,
        )

        # Verify history was passed to the API
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 4  # system + 2 history + 1 new

    @patch("services.assistant.MediaProcessor")
    @patch("services.assistant.format_for_llm")
    def test_with_media_files(self, mock_format, mock_processor_class):
        """Test processing with media files."""
        # Setup media processor mock
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        mock_processing_result = MagicMock()
        mock_processing_result.processing_summary.total_files = 1
        mock_processing_result.processing_summary.successful = 1
        mock_processing_result.processing_summary.failed = 0
        mock_processor.process.return_value = mock_processing_result

        # Setup formatter mock
        mock_format.return_value = {
            "role": "user",
            "content": [
                {"type": "text", "text": "User message\n\n[SOURCE: doc.pdf]\nContent"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,abc"}}
            ]
        }

        # Setup LLM response
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I see the damage report.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="Analyze this report",
            enriched_form_state={},
            files=[{
                "data": "base64pdfdata",
                "type": "pdf",
                "filename": "report.pdf"
            }],
            client=mock_client,
        )

        # Verify media processor was called
        mock_processor.process.assert_called_once()

        # Verify formatter was called
        mock_format.assert_called_once()

        # Verify response includes processing summary
        assert "processing_summary" in result
        assert result["processing_summary"]["total_files"] == 1
        assert result["processing_summary"]["successful"] == 1

    @patch("services.assistant.MediaProcessor")
    @patch("services.assistant.format_for_llm")
    def test_multimodal_content_passed_to_llm(self, mock_format, mock_processor_class):
        """Test that multimodal content from formatter is passed to LLM."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processing_result = MagicMock()
        mock_processing_result.processing_summary.total_files = 1
        mock_processing_result.processing_summary.successful = 1
        mock_processing_result.processing_summary.failed = 0
        mock_processor.process.return_value = mock_processing_result

        multimodal_content = [
            {"type": "text", "text": "Test\n\n[SOURCE: image.jpg]"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,xyz"}}
        ]
        mock_format.return_value = {"role": "user", "content": multimodal_content}

        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Image received.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        process_user_input(
            user_message="Look at this",
            enriched_form_state={},
            files=[{
                "data": "base64imagedata",
                "type": "image",
                "filename": "photo.jpg"
            }],
            client=mock_client,
        )

        # Verify the multimodal content was sent to the API
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        user_msg = messages[-1]

        assert user_msg["content"] == multimodal_content

    @patch("services.assistant.MediaProcessor")
    @patch("services.assistant.format_for_llm")
    def test_multiple_files(self, mock_format, mock_processor_class):
        """Test processing multiple files."""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processing_result = MagicMock()
        mock_processing_result.processing_summary.total_files = 3
        mock_processing_result.processing_summary.successful = 2
        mock_processing_result.processing_summary.failed = 1
        mock_processor.process.return_value = mock_processing_result

        mock_format.return_value = {"role": "user", "content": [{"type": "text", "text": "Combined"}]}

        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Processed files.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="Review these",
            enriched_form_state={},
            files=[
                {"data": "pdf1", "type": "pdf", "filename": "doc1.pdf"},
                {"data": "pdf2", "type": "pdf", "filename": "doc2.pdf"},
                {"data": "img1", "type": "image", "filename": "photo.jpg"},
            ],
            client=mock_client,
        )

        assert result["processing_summary"]["total_files"] == 3
        assert result["processing_summary"]["successful"] == 2
        assert result["processing_summary"]["failed"] == 1

    def test_empty_files_list_treated_as_text_only(self):
        """Test that empty files list is treated as text-only."""
        response = json.dumps({
            "classification": "QUESTION",
            "reply": "Sure, I can help.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="What is DREF?",
            enriched_form_state={},
            files=[],
            client=mock_client,
        )

        assert "processing_summary" not in result

    def test_form_state_passed_through(self):
        """Test that form state is included in system prompt."""
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Updated.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        enriched_form_state = {
            "operation_overview.country": {
                "value": "Nepal",
                "source": "user_message",
                "timestamp": "2024-01-01T00:00:00",
            },
            "operation_overview.disaster_type": {
                "value": "Earthquake",
                "source": "user_message",
                "timestamp": "2024-01-01T00:00:00",
            },
        }

        process_user_input(
            user_message="The magnitude was 7.2",
            enriched_form_state=enriched_form_state,
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]

        assert "Nepal" in system_prompt
        assert "Earthquake" in system_prompt

    def test_conflict_detection_with_enriched_state(self):
        """Test that conflicts are detected when enriched form state has existing values."""
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I see the population is 7500.",
            "field_updates": [
                {"field_id": "event_detail.total_affected_population", "value": 7500},
            ]
        })
        mock_client = self._create_mock_client(response)

        enriched_form_state = {
            "event_detail.total_affected_population": {
                "value": 5000,
                "source": "previous_report.pdf",
                "timestamp": "2024-01-01T00:00:00",
            }
        }

        result = process_user_input(
            user_message="The affected population is 7500",
            enriched_form_state=enriched_form_state,
            client=mock_client,
        )

        # Should detect a conflict since 5000 != 7500
        assert "conflicts" in result
        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["field_name"] == "event_detail.total_affected_population"

    def test_no_conflict_with_empty_form_state(self):
        """Test no conflicts when form state is empty."""
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted the flood.",
            "field_updates": [
                {"field_id": "operation_overview.disaster_type", "value": "Flood"},
            ]
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="There was a flood",
            enriched_form_state={},
            client=mock_client,
        )

        assert result["conflicts"] == []
        assert len(result["field_updates"]) == 1
        # Enriched updates should have source and timestamp
        assert "source" in result["field_updates"][0]
        assert "timestamp" in result["field_updates"][0]
        assert "field_id" in result["field_updates"][0]

    @patch("services.assistant.MediaProcessor")
    @patch("services.assistant.format_for_llm")
    def test_per_document_source_propagated(self, mock_format, mock_processor_class):
        """Test that per-update source from LLM is preserved in enriched updates."""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processing_result = MagicMock()
        mock_processing_result.processing_summary.total_files = 2
        mock_processing_result.processing_summary.successful = 2
        mock_processing_result.processing_summary.failed = 0
        mock_processor.process.return_value = mock_processing_result

        mock_format.return_value = {"role": "user", "content": [{"type": "text", "text": "Combined"}]}

        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Extracted from both documents.",
            "field_updates": [
                {"field_id": "operation_overview.country", "value": "Sudan", "source": "report.pdf"},
                {"field_id": "operation_overview.disaster_type", "value": "Flood", "source": "assessment.docx"},
            ]
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="Extract info from both.",
            enriched_form_state={},
            files=[
                {"data": "pdf1", "type": "pdf", "filename": "report.pdf"},
                {"data": "docx1", "type": "docx", "filename": "assessment.docx"},
            ],
            client=mock_client,
        )

        updates = {u["field_id"]: u["source"] for u in result["field_updates"]}
        assert updates["operation_overview.country"] == "report.pdf"
        assert updates["operation_overview.disaster_type"] == "assessment.docx"

    @patch("services.assistant.MediaProcessor")
    @patch("services.assistant.format_for_llm")
    def test_fallback_source_when_llm_omits_source(self, mock_format, mock_processor_class):
        """Test that fallback source is used when LLM doesn't include per-update source."""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processing_result = MagicMock()
        mock_processing_result.processing_summary.total_files = 2
        mock_processing_result.processing_summary.successful = 2
        mock_processing_result.processing_summary.failed = 0
        mock_processor.process.return_value = mock_processing_result

        mock_format.return_value = {"role": "user", "content": [{"type": "text", "text": "Combined"}]}

        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Extracted.",
            "field_updates": [
                {"field_id": "operation_overview.country", "value": "Sudan"},
            ]
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="Extract info.",
            enriched_form_state={},
            files=[
                {"data": "pdf1", "type": "pdf", "filename": "report.pdf"},
                {"data": "docx1", "type": "docx", "filename": "assessment.docx"},
            ],
            client=mock_client,
        )

        assert result["field_updates"][0]["source"] == "report.pdf, assessment.docx"

    @patch("services.assistant.MediaProcessor")
    @patch("services.assistant.format_for_llm")
    def test_conflict_shows_per_document_source(self, mock_format, mock_processor_class):
        """Test that conflicts against existing state show per-document source."""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processing_result = MagicMock()
        mock_processing_result.processing_summary.total_files = 1
        mock_processing_result.processing_summary.successful = 1
        mock_processing_result.processing_summary.failed = 0
        mock_processor.process.return_value = mock_processing_result

        mock_format.return_value = {"role": "user", "content": [{"type": "text", "text": "Content"}]}

        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Found different number.",
            "field_updates": [
                {"field_id": "event_detail.total_affected_population", "value": 15000, "source": "assessment.docx"},
            ]
        })
        mock_client = self._create_mock_client(response)

        result = process_user_input(
            user_message="Extract info.",
            enriched_form_state={
                "event_detail.total_affected_population": {
                    "value": 12500,
                    "source": "report.pdf",
                    "timestamp": "2026-03-09T00:00:00Z",
                }
            },
            files=[{"data": "docx1", "type": "docx", "filename": "assessment.docx"}],
            client=mock_client,
        )

        assert len(result["conflicts"]) == 1
        conflict = result["conflicts"][0]
        assert conflict["existing_value"]["source"] == "report.pdf"
        assert conflict["new_value"]["source"] == "assessment.docx"
