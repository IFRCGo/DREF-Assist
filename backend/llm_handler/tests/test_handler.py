"""Tests for the main LLM handler module."""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch

from llm_handler.handler import handle_message


class TestHandleMessage:
    """Tests for the main handle_message function."""

    def _create_mock_client(self, response_content: str):
        """Helper to create a mock OpenAI client with specified response."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()

        mock_message.content = response_content
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        return mock_client

    def test_basic_text_message_flow(self):
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I've noted the flood in Bangladesh.",
            "field_updates": [
                {"field_id": "operation_overview.disaster_type", "value": "Flood"},
            ]
        })
        mock_client = self._create_mock_client(response)

        result = handle_message(
            user_message="There was a flood in Bangladesh",
            current_form_state={},
            client=mock_client,
        )

        assert result["classification"] == "NEW_INFORMATION"
        assert "Bangladesh" in result["reply"]
        assert len(result["field_updates"]) == 1

    def test_multimodal_message_from_media_processor(self):
        """Test handling of multimodal content from media-processor formatter."""
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I see the flood damage in the images.",
            "field_updates": [
                {"field_id": "operation_overview.disaster_type", "value": "Flood"},
            ]
        })
        mock_client = self._create_mock_client(response)

        # Multimodal content as produced by media-processor's formatter
        multimodal_message = [
            {
                "type": "text",
                "text": "[SOURCE: report.pdf]\nFlooding observed in the region.\n[PDF_1_IMAGE_1]"
            },
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQ..."}
            }
        ]

        result = handle_message(
            user_message=multimodal_message,
            current_form_state={},
            client=mock_client,
        )

        # Verify the API was called with the multimodal content
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # Last message should have our multimodal content
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == multimodal_message

        assert result["classification"] == "NEW_INFORMATION"

    def test_includes_conversation_history(self):
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

        result = handle_message(
            user_message="Actually it's 7500",
            current_form_state={"event_detail.total_affected_population": 5000},
            conversation_history=history,
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # Should have: system, user (history), assistant (history), user (new)
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "Actually it's 7500"

    def test_form_state_included_in_system_prompt(self):
        response = json.dumps({
            "classification": "QUESTION",
            "reply": "Some answer",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        form_state = {
            "operation_overview.country": "Nepal",
            "operation_overview.disaster_type": "Earthquake",
        }

        handle_message(
            user_message="What's next?",
            current_form_state=form_state,
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]

        assert "Nepal" in system_prompt
        assert "Earthquake" in system_prompt

    def test_uses_gpt4o_model(self):
        response = json.dumps({
            "classification": "OFF_TOPIC",
            "reply": "Let's focus on DREF.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        handle_message(
            user_message="What's the weather?",
            current_form_state={},
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args

        assert call_args.kwargs["model"] == "gpt-4o"

    def test_uses_low_temperature(self):
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        handle_message(
            user_message="Test",
            current_form_state={},
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args

        assert call_args.kwargs["temperature"] == 0.1

    def test_uses_json_response_format(self):
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        handle_message(
            user_message="Test",
            current_form_state={},
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args

        assert call_args.kwargs["response_format"] == {"type": "json_object"}

    def test_validates_field_updates(self):
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "operation_overview.disaster_type", "value": "Flood"},
                {"field_id": "invalid.field", "value": "bad"},  # Should be filtered
                {"field_id": "event_detail.total_affected_population", "value": "not a number"},  # Filtered
            ]
        })
        mock_client = self._create_mock_client(response)

        result = handle_message(
            user_message="Flood affected many",
            current_form_state={},
            client=mock_client,
        )

        # Only the valid update should remain
        assert len(result["field_updates"]) == 1
        assert result["field_updates"][0]["field_id"] == "operation_overview.disaster_type"

    def test_handles_api_error_gracefully(self):
        # Simulate API returning None content
        mock_client = self._create_mock_client(None)

        # This should not raise, should return error response
        result = handle_message(
            user_message="Test",
            current_form_state={},
            client=mock_client,
        )

        assert result["classification"] == "ERROR"

    def test_empty_history_handled(self):
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        result = handle_message(
            user_message="Test",
            current_form_state={},
            conversation_history=[],
            client=mock_client,
        )

        assert result["classification"] == "NEW_INFORMATION"

    def test_none_history_handled(self):
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        result = handle_message(
            user_message="Test",
            current_form_state={},
            conversation_history=None,
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # Should only have system + user (no history)
        assert len(messages) == 2


class TestMediaProcessorIntegration:
    """Tests verifying integration with media-processor output format."""

    def _create_mock_client(self, response_content: str):
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()

        mock_message.content = response_content
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        return mock_client

    def test_handles_format_from_formatter(self):
        """
        Test that the handler accepts output from media-processor's format_for_llm.

        The formatter produces messages like:
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "User message\n\n[SOURCE: file.pdf]\n..."},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
            ]
        }
        """
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I see the damage assessment shows significant flooding.",
            "field_updates": [
                {"field_id": "operation_overview.disaster_type", "value": "Flood"},
                {"field_id": "event_detail.total_affected_population", "value": 10000},
            ]
        })
        mock_client = self._create_mock_client(response)

        # Simulated output from media-processor formatter (the content part)
        formatted_content = [
            {
                "type": "text",
                "text": (
                    "Please analyze this damage report\n\n---\n\n"
                    "[SOURCE: damage_report.pdf]\n"
                    "Flood Impact Assessment\n"
                    "Date: 2024-01-15\n"
                    "Affected Population: 10,000\n"
                    "[PDF_1_IMAGE_1]\n"
                    "The image above shows the water levels.\n"
                    "[PDF_1_IMAGE_2]\n"
                    "Aerial view of affected areas."
                )
            },
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQbase64image1"}
            },
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQbase64image2"}
            }
        ]

        result = handle_message(
            user_message=formatted_content,
            current_form_state={},
            client=mock_client,
        )

        # Verify API was called correctly
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        user_msg = messages[-1]

        assert user_msg["role"] == "user"
        assert user_msg["content"] == formatted_content
        assert len(user_msg["content"]) == 3

        # Verify response processed correctly
        assert result["classification"] == "NEW_INFORMATION"
        assert len(result["field_updates"]) == 2

    def test_mixed_history_with_multimodal_current(self):
        """Test history with text messages + current multimodal message."""
        response = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I've added the video evidence.",
            "field_updates": []
        })
        mock_client = self._create_mock_client(response)

        history = [
            {"role": "user", "content": "We're documenting a flood"},
            {"role": "assistant", "content": "I'll help you document the flood."},
        ]

        # Current message is multimodal (from video with frames)
        current_multimodal = [
            {
                "type": "text",
                "text": "[SOURCE: field_video.mp4]\nTranscript: Heavy flooding visible...\n[VIDEO_1_FRAME_1]"
            },
            {
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64,videoframe1"}
            }
        ]

        result = handle_message(
            user_message=current_multimodal,
            current_form_state={"operation_overview.disaster_type": "Flood"},
            conversation_history=history,
            client=mock_client,
        )

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # system + 2 history + 1 current = 4
        assert len(messages) == 4
        assert messages[-1]["content"] == current_multimodal
