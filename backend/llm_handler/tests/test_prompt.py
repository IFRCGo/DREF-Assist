"""Tests for the system prompt construction module."""

import pytest
import json

from llm_handler.prompt import (
    build_system_prompt,
    ROLE_DEFINITION,
    BEHAVIOR_INSTRUCTIONS,
    FIELD_SCHEMA_REFERENCE,
)
from llm_handler.field_schema import VALID_FIELD_IDS, DROPDOWN_OPTIONS, FIELD_METADATA


class TestBuildSystemPrompt:
    """Tests for system prompt construction."""

    def test_contains_role_definition(self):
        prompt = build_system_prompt({})

        assert "DREF" in prompt
        assert "Disaster Relief Emergency Fund" in prompt
        assert "IFRC" in prompt

    def test_contains_form_state_as_json(self):
        form_state = {
            "operation_overview.country": "Bangladesh",
            "event_detail.total_affected_population": 5000,
        }

        prompt = build_system_prompt(form_state)

        assert '"operation_overview.country": "Bangladesh"' in prompt
        assert '"event_detail.total_affected_population": 5000' in prompt

    def test_empty_form_state_shows_empty_object(self):
        prompt = build_system_prompt({})

        assert "{}" in prompt

    def test_contains_field_schema_reference(self):
        prompt = build_system_prompt({})

        assert "Available fields you can update" in prompt
        assert "operation_overview" in prompt
        assert "event_detail" in prompt

    def test_dropdown_options_included(self):
        prompt = build_system_prompt({})

        # Check that dropdown options are included
        assert '"Imminent Crisis"' in prompt
        assert '"Response"' in prompt
        assert '"Protracted Crisis"' in prompt
        assert '"Flood"' in prompt
        assert '"Earthquake"' in prompt

    def test_field_types_documented(self):
        prompt = build_system_prompt({})

        assert "(boolean" in prompt
        assert "(number" in prompt
        assert "(date, ISO format YYYY-MM-DD" in prompt
        assert "(text" in prompt
        assert "(dropdown" in prompt

    def test_contains_classification_instructions(self):
        prompt = build_system_prompt({})

        assert "CLASSIFY" in prompt
        assert "NEW_INFORMATION" in prompt
        assert "MODIFICATION_REQUEST" in prompt
        assert "QUESTION" in prompt
        assert "OFF_TOPIC" in prompt

    def test_contains_tiered_extraction_rules(self):
        prompt = build_system_prompt({})

        assert "FACTUAL" in prompt
        assert "INFERRED" in prompt
        assert "SYNTHESIZED" in prompt
        assert "EXTRACTION RULES BY FIELD CATEGORY" in prompt

    def test_factual_rules_prevent_fabrication(self):
        prompt = build_system_prompt({})

        assert "Never guess or fabricate" in prompt
        assert "Never infer demographics" in prompt
        assert "Never assume dates" in prompt

    def test_inferred_rules_allow_deduction(self):
        prompt = build_system_prompt({})

        assert "MAY logically deduce" in prompt

    def test_synthesized_rules_encourage_composition(self):
        prompt = build_system_prompt({})

        assert "SHOULD actively compose" in prompt

    def test_field_descriptions_in_prompt(self):
        prompt = build_system_prompt({})

        for field_id, meta in FIELD_METADATA.items():
            assert meta["description"] in prompt, (
                f"Description for {field_id} not found in prompt"
            )

    def test_field_extraction_hints_in_prompt(self):
        prompt = build_system_prompt({})

        for field_id, meta in FIELD_METADATA.items():
            assert meta["extraction_hint"] in prompt, (
                f"Extraction hint for {field_id} not found in prompt"
            )

    def test_field_categories_in_schema_reference(self):
        for field_id, meta in FIELD_METADATA.items():
            category_upper = meta["category"].upper()
            assert category_upper in FIELD_SCHEMA_REFERENCE, (
                f"Category {category_upper} for {field_id} not in schema reference"
            )

    def test_contains_json_format_instructions(self):
        prompt = build_system_prompt({})

        assert "JSON format" in prompt
        assert '"classification"' in prompt
        assert '"reply"' in prompt
        assert '"field_updates"' in prompt
        assert '"field_id"' in prompt

    def test_all_valid_fields_documented(self):
        prompt = build_system_prompt({})

        for field_id in VALID_FIELD_IDS:
            _, field_name = field_id.split(".", 1)
            assert field_name in prompt, f"Field {field_name} not in prompt"

    def test_form_state_with_special_characters(self):
        form_state = {
            "event_detail.what_happened": 'Flood with "heavy" rain & wind',
        }

        prompt = build_system_prompt(form_state)

        # JSON should properly escape quotes
        assert "Flood with" in prompt
        assert "heavy" in prompt

    def test_unicode_in_form_state_preserved(self):
        form_state = {
            "operation_overview.region_province": "São Paulo",
        }

        prompt = build_system_prompt(form_state)

        # ensure_ascii=False should preserve Unicode
        assert "São Paulo" in prompt


class TestFieldSchemaReference:
    """Tests for the pre-computed field schema reference."""

    def test_schema_is_precomputed(self):
        # FIELD_SCHEMA_REFERENCE should be a string computed at module load
        assert isinstance(FIELD_SCHEMA_REFERENCE, str)
        assert len(FIELD_SCHEMA_REFERENCE) > 0

    def test_schema_groups_by_tab(self):
        assert "operation_overview:" in FIELD_SCHEMA_REFERENCE
        assert "event_detail:" in FIELD_SCHEMA_REFERENCE

    def test_schema_includes_all_dropdown_options(self):
        for field_id, options in DROPDOWN_OPTIONS.items():
            for option in options:
                assert f'"{option}"' in FIELD_SCHEMA_REFERENCE, (
                    f"Option {option} for {field_id} not in schema"
                )


class TestFieldMetadata:
    """Tests for field metadata completeness and validity."""

    VALID_CATEGORIES = {"factual", "inferred", "synthesized"}
    REQUIRED_KEYS = {"category", "description", "extraction_hint"}

    def test_every_field_has_metadata(self):
        for field_id in VALID_FIELD_IDS:
            assert field_id in FIELD_METADATA, (
                f"Field {field_id} missing from FIELD_METADATA"
            )

    def test_no_extra_fields_in_metadata(self):
        for field_id in FIELD_METADATA:
            assert field_id in VALID_FIELD_IDS, (
                f"FIELD_METADATA has unknown field {field_id}"
            )

    def test_all_required_keys_present(self):
        for field_id, meta in FIELD_METADATA.items():
            for key in self.REQUIRED_KEYS:
                assert key in meta, (
                    f"Field {field_id} missing key '{key}' in FIELD_METADATA"
                )

    def test_categories_are_valid(self):
        for field_id, meta in FIELD_METADATA.items():
            assert meta["category"] in self.VALID_CATEGORIES, (
                f"Field {field_id} has invalid category '{meta['category']}'"
            )

    def test_descriptions_are_nonempty_strings(self):
        for field_id, meta in FIELD_METADATA.items():
            assert isinstance(meta["description"], str) and len(meta["description"]) > 10, (
                f"Field {field_id} has empty or too-short description"
            )

    def test_extraction_hints_are_nonempty_strings(self):
        for field_id, meta in FIELD_METADATA.items():
            assert isinstance(meta["extraction_hint"], str) and len(meta["extraction_hint"]) > 10, (
                f"Field {field_id} has empty or too-short extraction_hint"
            )


class TestPromptConstants:
    """Tests for prompt constant definitions."""

    def test_role_definition_not_empty(self):
        assert len(ROLE_DEFINITION) > 50

    def test_behavior_instructions_not_empty(self):
        assert len(BEHAVIOR_INSTRUCTIONS) > 100

    def test_behavior_instructions_includes_json_schema(self):
        assert "field_id" in BEHAVIOR_INSTRUCTIONS
        assert "tab.field_name" in BEHAVIOR_INSTRUCTIONS
