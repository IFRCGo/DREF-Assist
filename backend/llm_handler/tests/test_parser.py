"""Tests for the LLM response parser module."""

import json

from llm_handler.parser import (
    parse_llm_response,
    process_llm_response,
    VALID_CLASSIFICATIONS,
)


class TestParseLLMResponse:
    """Tests for JSON extraction from raw LLM responses."""

    def test_valid_json_response(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Got it!",
            "field_updates": []
        })

        result = parse_llm_response(raw)

        assert result["classification"] == "NEW_INFORMATION"
        assert result["reply"] == "Got it!"
        assert result["field_updates"] == []

    def test_json_wrapped_in_markdown_code_block(self):
        raw = '''```json
{
    "classification": "QUESTION",
    "reply": "Happy to help!",
    "field_updates": []
}
```'''

        result = parse_llm_response(raw)

        assert result["classification"] == "QUESTION"
        assert result["reply"] == "Happy to help!"

    def test_json_wrapped_in_plain_code_block(self):
        raw = '''```
{"classification": "OFF_TOPIC", "reply": "Let's focus on DREF.", "field_updates": []}
```'''

        result = parse_llm_response(raw)

        assert result["classification"] == "OFF_TOPIC"

    def test_invalid_json_returns_error_response(self):
        raw = "This is not valid JSON at all"

        result = parse_llm_response(raw)

        assert result["classification"] == "ERROR"
        assert "trouble processing" in result["reply"]
        assert result["field_updates"] == []

    def test_empty_string_returns_error_response(self):
        result = parse_llm_response("")

        assert result["classification"] == "ERROR"

    def test_whitespace_only_returns_error_response(self):
        result = parse_llm_response("   \n\t  ")

        assert result["classification"] == "ERROR"

    def test_json_array_returns_error_response(self):
        raw = '["not", "an", "object"]'

        result = parse_llm_response(raw)

        assert result["classification"] == "ERROR"

    def test_partial_json_returns_error_response(self):
        raw = '{"classification": "NEW_INFORMATION", "reply":'

        result = parse_llm_response(raw)

        assert result["classification"] == "ERROR"

    def test_nested_code_blocks_handled(self):
        raw = '''```json
{
    "classification": "NEW_INFORMATION",
    "reply": "Here is some code: ```print('hello')```",
    "field_updates": []
}
```'''
        # The inner code block in reply is just a string, should parse fine
        result = parse_llm_response(raw)

        assert result["classification"] == "NEW_INFORMATION"
        assert "code" in result["reply"]


class TestProcessLLMResponse:
    """Tests for complete response processing with validation."""

    def test_valid_response_passes_through(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "I've recorded the flood in Bangladesh.",
            "field_updates": [
                {"field_id": "operation_overview.disaster_type", "value": "Flood"},
                {"field_id": "operation_overview.country", "value": "Bangladesh"},
            ]
        })

        result = process_llm_response(raw)

        assert result["classification"] == "NEW_INFORMATION"
        assert "Bangladesh" in result["reply"]
        # Both pass: disaster_type is valid dropdown, country has no defined options so any value allowed
        assert len(result["field_updates"]) == 2
        assert result["field_updates"][0]["value"] == "Flood"
        assert result["field_updates"][1]["value"] == "Bangladesh"

    def test_invalid_classification_becomes_error(self):
        raw = json.dumps({
            "classification": "MADE_UP_TYPE",
            "reply": "Something",
            "field_updates": []
        })

        result = process_llm_response(raw)

        assert result["classification"] == "ERROR"

    def test_missing_classification_becomes_error(self):
        raw = json.dumps({
            "reply": "Something",
            "field_updates": []
        })

        result = process_llm_response(raw)

        assert result["classification"] == "ERROR"

    def test_invalid_field_id_filtered_out(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "fake_section.fake_field", "value": "something"},
                {"field_id": "operation_overview.disaster_type", "value": "Earthquake"},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 1
        assert result["field_updates"][0]["field_id"] == "operation_overview.disaster_type"

    def test_invalid_dropdown_value_filtered_out(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "operation_overview.dref_type", "value": "Invalid Type"},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 0

    def test_valid_dropdown_value_passes(self):
        raw = json.dumps({
            "classification": "MODIFICATION_REQUEST",
            "reply": "Updated.",
            "field_updates": [
                {"field_id": "operation_overview.dref_type", "value": "Response"},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 1
        assert result["field_updates"][0]["value"] == "Response"

    def test_boolean_field_requires_boolean(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "operation_overview.emergency_appeal_planned", "value": "yes"},
            ]
        })

        result = process_llm_response(raw)

        # "yes" is not a boolean, should be filtered
        assert len(result["field_updates"]) == 0

    def test_boolean_field_accepts_boolean(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "operation_overview.emergency_appeal_planned", "value": True},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 1
        assert result["field_updates"][0]["value"] is True

    def test_number_field_requires_number(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "event_detail.total_affected_population", "value": "5000"},
            ]
        })

        result = process_llm_response(raw)

        # "5000" is a string, should be filtered
        assert len(result["field_updates"]) == 0

    def test_number_field_accepts_int(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "event_detail.total_affected_population", "value": 5000},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 1
        assert result["field_updates"][0]["value"] == 5000

    def test_number_field_accepts_float(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "event_detail.people_in_need", "value": 2500.5},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 1

    def test_date_field_validates_format(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "event_detail.date_trigger_met", "value": "January 15, 2024"},
            ]
        })

        result = process_llm_response(raw)

        # Invalid date format, should be filtered
        assert len(result["field_updates"]) == 0

    def test_date_field_accepts_iso_format(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "event_detail.date_trigger_met", "value": "2024-01-15"},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 1
        assert result["field_updates"][0]["value"] == "2024-01-15"

    def test_text_field_accepts_string(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "event_detail.what_happened", "value": "Major flooding occurred."},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 1
        assert "flooding" in result["field_updates"][0]["value"]

    def test_text_field_rejects_non_string(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Noted.",
            "field_updates": [
                {"field_id": "event_detail.what_happened", "value": 12345},
            ]
        })

        result = process_llm_response(raw)

        assert len(result["field_updates"]) == 0

    def test_non_string_reply_converted(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": None,
            "field_updates": []
        })

        result = process_llm_response(raw)

        assert result["reply"] == ""

    def test_field_updates_not_list_becomes_empty(self):
        raw = json.dumps({
            "classification": "NEW_INFORMATION",
            "reply": "Something",
            "field_updates": "not a list"
        })

        result = process_llm_response(raw)

        assert result["field_updates"] == []

    def test_all_valid_classifications_accepted(self):
        for classification in VALID_CLASSIFICATIONS:
            raw = json.dumps({
                "classification": classification,
                "reply": "Test",
                "field_updates": []
            })

            result = process_llm_response(raw)

            assert result["classification"] == classification
