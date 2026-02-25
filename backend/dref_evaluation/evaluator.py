"""
DREF Evaluator Module

This module implements the two-pass evaluation system for DREF applications:
- Pass 1: Rubric Scoring - Evaluates form state against rubric criteria
- Pass 2: Comparative Analysis - Uses reference examples for improvement suggestions (only if needed)
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class CriterionResult:
    """Result of evaluating a single criterion."""
    criterion_id: str
    field: str
    criterion: str
    outcome: str  # 'accept' or 'dont_accept'
    required: bool
    reasoning: str = ""
    improvement_prompt: str = ""
    guidance: str = ""


@dataclass
class SectionResult:
    """Result of evaluating a section."""
    section_name: str
    section_display_name: str
    status: str  # 'accept' or 'needs_revision'
    criteria_results: Dict[str, CriterionResult] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """Complete evaluation result for a DREF application."""
    dref_id: int
    overall_status: str = 'pending'  # 'accepted', 'needs_revision', or 'pending'
    section_results: Dict[str, SectionResult] = field(default_factory=dict)
    improvement_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    pass_one_completed: bool = False
    pass_two_completed: bool = False
    reference_examples_used: List[int] = field(default_factory=list)


class RubricLoader:
    """Loads and provides access to the evaluation rubric."""

    _instance = None
    _rubric = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._rubric is None:
            self._load_rubric()

    def _load_rubric(self):
        """Load the rubric from the JSON file."""
        rubric_path = Path(__file__).parent / 'evaluation_rubric.json'
        with open(rubric_path, 'r', encoding='utf-8-sig') as f:
            self._rubric = json.load(f)

    @property
    def rubric(self) -> Dict:
        return self._rubric

    def get_section(self, section_name: str) -> Optional[Dict]:
        """Get criteria for a specific section."""
        return self._rubric.get('sections', {}).get(section_name)

    def get_all_sections(self) -> Dict:
        """Get all sections."""
        return self._rubric.get('sections', {})

    def get_section_criteria(self, section_name: str) -> List[Dict]:
        """Get criteria for a specific section."""
        section = self.get_section(section_name)
        return section.get('criteria', []) if section else []


class DrefEvaluator:
    """
    Main evaluator class that performs two-pass evaluation of DREF applications.
    """

    def __init__(self, llm_client=None):
        """
        Initialize the evaluator.

        Args:
            llm_client: Optional LLM client for AI-powered evaluation.
                       If not provided, uses rule-based evaluation.
        """
        self.rubric = RubricLoader()
        self.llm_client = llm_client

    def evaluate(self, dref_id: int, form_state: Dict[str, Any]) -> EvaluationResult:
        """
        Perform complete evaluation of a DREF application.

        Args:
            dref_id: ID of the DREF application
            form_state: Current state of the DREF form

        Returns:
            EvaluationResult with complete evaluation details
        """
        result = EvaluationResult(dref_id=dref_id)

        # Pass 1: Rubric Scoring
        result = self._pass_one_rubric_scoring(result, form_state)
        result.pass_one_completed = True

        # Pass 2: Comparative Analysis (only if there are issues)
        if result.overall_status == 'needs_revision':
            result = self._pass_two_comparative_analysis(result, form_state)
            result.pass_two_completed = True

        return result

    def evaluate_section(
        self,
        section_name: str,
        form_state: Dict[str, Any],
        dref_id: int = 0
    ) -> SectionResult:
        """
        Evaluate a single section of the DREF form.

        Args:
            section_name: Name of the section to evaluate
            form_state: Current state of the DREF form
            dref_id: Optional DREF ID for context

        Returns:
            SectionResult with evaluation details for the section
        """
        section_config = self.rubric.get_section(section_name)
        if not section_config:
            raise ValueError(f"Unknown section: {section_name}")

        section_result = SectionResult(
            section_name=section_name,
            section_display_name=section_config.get('name', section_name),
            status='accept'
        )

        criteria = section_config.get('criteria', [])
        for criterion in criteria:
            criterion_result = self._evaluate_criterion(criterion, form_state)
            section_result.criteria_results[criterion['id']] = criterion_result

            if criterion_result.outcome == 'dont_accept':
                section_result.issues.append(criterion_result.criterion)
                if criterion_result.required:
                    section_result.status = 'needs_revision'

        return section_result

    def _pass_one_rubric_scoring(
        self,
        result: EvaluationResult,
        form_state: Dict[str, Any]
    ) -> EvaluationResult:
        """
        Pass 1: Evaluate form state against rubric criteria.
        No reference examples used to prevent hallucination.
        """
        all_sections = self.rubric.get_all_sections()
        has_required_failures = False

        for section_name, section_config in all_sections.items():
            section_result = self.evaluate_section(section_name, form_state)
            result.section_results[section_name] = section_result

            if section_result.status == 'needs_revision':
                has_required_failures = True

        result.overall_status = 'needs_revision' if has_required_failures else 'accepted'
        return result

    def _pass_two_comparative_analysis(
        self,
        result: EvaluationResult,
        form_state: Dict[str, Any]
    ) -> EvaluationResult:
        """
        Pass 2: Comparative analysis using reference examples.
        Only runs if Pass 1 identifies issues.
        """
        # Collect weak fields
        weak_fields = self._collect_weak_fields(result)

        # Generate improvement suggestions based on weak fields
        for weak_field in weak_fields:
            suggestion = self._generate_improvement_suggestion(weak_field, form_state)
            if suggestion:
                result.improvement_suggestions.append(suggestion)

        # Sort suggestions by priority
        result.improvement_suggestions.sort(
            key=lambda x: x.get('priority', 999)
        )

        return result

    def _evaluate_criterion(
        self,
        criterion: Dict,
        form_state: Dict[str, Any]
    ) -> CriterionResult:
        """
        Evaluate a single criterion against the form state.
        """
        criterion_id = criterion['id']
        field_name = criterion['field']
        required = criterion.get('required', True)

        # Check if criterion has a condition
        condition = criterion.get('condition')
        if condition and not self._check_condition(condition, form_state):
            # Condition not met, criterion doesn't apply
            return CriterionResult(
                criterion_id=criterion_id,
                field=field_name,
                criterion=criterion['criterion'],
                outcome='accept',
                required=required,
                reasoning="Criterion not applicable based on form conditions",
                guidance=criterion.get('guidance', '')
            )

        # Get field value from form state
        field_value = self._get_field_value(field_name, form_state)

        # Evaluate the field
        outcome, reasoning = self._evaluate_field_value(
            field_name,
            field_value,
            criterion
        )

        # Generate improvement prompt if needed
        improvement_prompt = ""
        if outcome == 'dont_accept':
            improvement_prompt = self._generate_criterion_prompt(criterion, field_value)

        return CriterionResult(
            criterion_id=criterion_id,
            field=field_name,
            criterion=criterion['criterion'],
            outcome=outcome,
            required=required,
            reasoning=reasoning,
            improvement_prompt=improvement_prompt,
            guidance=criterion.get('guidance', '')
        )

    def _get_field_value(self, field_name: str, form_state: Dict[str, Any]) -> Any:
        """
        Get a field value from the form state.
        Supports nested field access with dot notation.
        """
        keys = field_name.split('.')
        value = form_state

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _evaluate_field_value(
        self,
        field_name: str,
        field_value: Any,
        criterion: Dict
    ) -> Tuple[str, str]:
        """
        Evaluate if a field value meets the criterion requirements.
        Returns (outcome, reasoning) tuple.
        Handles different field types: text, integer, boolean, date, M2M, FK.
        """
        # Get field type from rubric if available
        field_types = self.rubric.rubric.get('field_type_mapping', {})
        field_type = field_types.get(field_name, 'text')

        # Check if field is empty or missing
        if field_value is None:
            return ('dont_accept', f"Field '{field_name}' is missing or empty")

        # Handle boolean fields
        if field_type == 'boolean':
            if isinstance(field_value, bool):
                return ('accept', f"Field '{field_name}' has a valid boolean value")
            return ('dont_accept', f"Field '{field_name}' should be a boolean value")

        # Handle integer fields
        if field_type in ('integer', 'integer_choice'):
            if isinstance(field_value, (int, float)) and field_value is not None:
                if field_value >= 0:
                    return ('accept', f"Field '{field_name}' has a valid numeric value")
            return ('dont_accept', f"Field '{field_name}' should have a valid numeric value")

        # Handle date fields
        if field_type == 'date':
            if field_value:
                return ('accept', f"Field '{field_name}' has a date specified")
            return ('dont_accept', f"Field '{field_name}' should have a date specified")

        # Handle M2M fields (stored as lists or with .all() in ORM)
        if field_type in ('many_to_many', 'many_to_many_file'):
            if isinstance(field_value, list):
                if len(field_value) > 0:
                    return ('accept', f"Field '{field_name}' has {len(field_value)} item(s)")
                return ('dont_accept', f"Field '{field_name}' has no items selected")
            # Handle QuerySet-like objects
            if hasattr(field_value, 'count'):
                if field_value.count() > 0:
                    return ('accept', f"Field '{field_name}' has {field_value.count()} item(s)")
                return ('dont_accept', f"Field '{field_name}' has no items selected")
            if field_value:
                return ('accept', f"Field '{field_name}' has content")
            return ('dont_accept', f"Field '{field_name}' is empty")

        # Handle FK file fields
        if field_type == 'foreign_key_file':
            if field_value:
                return ('accept', f"Field '{field_name}' has a file attached")
            return ('dont_accept', f"Field '{field_name}' needs a file attachment")

        # Handle char fields (short text like names, emails)
        if field_type == 'char':
            if isinstance(field_value, str) and field_value.strip():
                return ('accept', f"Field '{field_name}' is provided")
            return ('dont_accept', f"Field '{field_name}' is empty")

        # Handle text fields (longer content)
        if isinstance(field_value, str):
            if not field_value.strip():
                return ('dont_accept', f"Field '{field_name}' is empty")

            # Check minimum content length for text fields (not char)
            if field_type == 'text' and len(field_value.strip()) < 20:
                return ('dont_accept', f"Field '{field_name}' has insufficient content (less than 20 characters)")

            return ('accept', f"Field '{field_name}' contains required content")

        if isinstance(field_value, list):
            if len(field_value) == 0:
                return ('dont_accept', f"Field '{field_name}' is empty (no items)")
            return ('accept', f"Field '{field_name}' has {len(field_value)} item(s)")

        if isinstance(field_value, dict):
            if not field_value:
                return ('dont_accept', f"Field '{field_name}' is empty (no data)")
            return ('accept', f"Field '{field_name}' contains data")

        # If we get here, basic validation passed
        return ('accept', f"Field '{field_name}' contains required content")

    def _check_condition(self, condition: str, form_state: Dict[str, Any]) -> bool:
        """
        Check if a condition for a criterion is met.
        Uses actual Dref model field names.
        """
        condition_checks = {
            # Check if DREF type is Imminent (type_of_dref == 0)
            'is_anticipatory': lambda fs: fs.get('type_of_dref') == 0 or fs.get('is_dref_imminent_v2', False),
            # Check if surge personnel is being requested
            'has_surge_request': lambda fs: fs.get('is_surge_personnel_deployed', False),
            # Check if other operations exist
            'has_other_operations': lambda fs: bool(fs.get('other_operations')),
        }

        check_func = condition_checks.get(condition)
        if check_func:
            return check_func(form_state)

        return True  # Unknown condition, assume met

    def _collect_weak_fields(self, result: EvaluationResult) -> List[Dict]:
        """
        Collect all fields that didn't pass evaluation.
        """
        weak_fields = []

        for section_name, section_result in result.section_results.items():
            for criterion_id, criterion_result in section_result.criteria_results.items():
                if criterion_result.outcome == 'dont_accept':
                    weak_fields.append({
                        'section': section_name,
                        'criterion_id': criterion_id,
                        'field': criterion_result.field,
                        'criterion': criterion_result.criterion,
                        'required': criterion_result.required,
                        'guidance': criterion_result.guidance
                    })

        return weak_fields

    def _generate_improvement_suggestion(
        self,
        weak_field: Dict,
        form_state: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Generate an improvement suggestion for a weak field.
        """
        priority = 1 if weak_field['required'] else 2

        return {
            'section': weak_field['section'],
            'field': weak_field['field'],
            'criterion': weak_field['criterion'],
            'priority': priority,
            'guidance': weak_field['guidance'],
            'ready_prompt': self._generate_criterion_prompt(weak_field, None),
            'auto_applicable': True
        }

    def _generate_criterion_prompt(
        self,
        criterion: Dict,
        current_value: Any
    ) -> str:
        """
        Generate a prompt that can be sent to the chat endpoint for improvement.
        """
        field = criterion.get('field', '')
        criterion_text = criterion.get('criterion', '')
        guidance = criterion.get('guidance', '')

        prompt = f"Please improve the '{field}' field to meet this criterion: {criterion_text}"
        if guidance:
            prompt += f"\n\nGuidance: {guidance}"

        return prompt

    def to_dict(self, result: EvaluationResult) -> Dict:
        """
        Convert an EvaluationResult to a dictionary for serialization.
        """
        return {
            'dref_id': result.dref_id,
            'overall_status': result.overall_status,
            'section_results': {
                section_name: {
                    'section_name': sr.section_name,
                    'section_display_name': sr.section_display_name,
                    'status': sr.status,
                    'criteria_results': {
                        cid: asdict(cr) for cid, cr in sr.criteria_results.items()
                    },
                    'issues': sr.issues
                }
                for section_name, sr in result.section_results.items()
            },
            'improvement_suggestions': result.improvement_suggestions,
            'pass_one_completed': result.pass_one_completed,
            'pass_two_completed': result.pass_two_completed,
            'reference_examples_used': result.reference_examples_used
        }


class AutoImprover:
    """
    Handles automatic improvement of DREF applications by routing
    improvement prompts to the existing chat endpoint.
    """

    def __init__(self, chat_endpoint_url: str = '/api/v2/chat'):
        """
        Initialize the auto-improver.

        Args:
            chat_endpoint_url: URL of the existing chat endpoint
        """
        self.chat_endpoint_url = chat_endpoint_url
        self.evaluator = DrefEvaluator()

    def auto_improve(
        self,
        dref_id: int,
        form_state: Dict[str, Any],
        max_improvements: int = 5
    ) -> Dict[str, Any]:
        """
        Automatically apply high-priority improvements.

        Args:
            dref_id: ID of the DREF application
            form_state: Current form state
            max_improvements: Maximum number of improvements to apply

        Returns:
            Dict with updated form state and new evaluation
        """
        # First evaluate
        evaluation_result = self.evaluator.evaluate(dref_id, form_state)

        # Get high-priority suggestions
        suggestions = evaluation_result.improvement_suggestions[:max_improvements]

        applied_improvements = []
        updated_form_state = form_state.copy()

        for suggestion in suggestions:
            if suggestion.get('auto_applicable'):
                # In a real implementation, this would call the chat endpoint
                # For now, we record that the improvement was suggested
                applied_improvements.append({
                    'field': suggestion['field'],
                    'prompt': suggestion['ready_prompt'],
                    'status': 'suggested'
                })

        # Re-evaluate after improvements (in real implementation)
        new_evaluation = self.evaluator.evaluate(dref_id, updated_form_state)

        return {
            'original_status': evaluation_result.overall_status,
            'new_status': new_evaluation.overall_status,
            'applied_improvements': applied_improvements,
            'updated_form_state': updated_form_state,
            'new_evaluation': self.evaluator.to_dict(new_evaluation)
        }


# Singleton instance for convenience
_evaluator_instance = None


def get_evaluator() -> DrefEvaluator:
    """Get the singleton evaluator instance."""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = DrefEvaluator()
    return _evaluator_instance
