"""
DREF Evaluator Module

This module implements the two-pass evaluation system for DREF applications:
- Pass 1: Rubric Scoring - Evaluates form state against rubric criteria
- Pass 2: Comparative Analysis - Uses reference examples for improvement suggestions (only if needed)
"""

import json
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path

from openai import RateLimitError, APITimeoutError

# LLM timeout and retry configuration
LLM_TIMEOUT = 30  # seconds - prevents hanging on Azure OpenAI calls
LLM_MAX_RETRIES = 3  # maximum number of retry attempts
LLM_RETRY_BASE_DELAY = 1  # seconds - initial delay for exponential backoff


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


# Rubric fields that use LLM-based quality evaluation (all are type 'text')
_LLM_EVALUATED_FIELDS: set = {
    "event_description",
    "event_scope",
    "ifrc",
    "icrc",
    "partner_national_society",
    "national_authorities",
    "identified_gaps",
    "operation_objective",
    "response_strategy",
    "selection_criteria",
    "people_assisted",
    "human_resource",
    "logistic_capacity_of_ns",
    "safety_concerns",
    "pmer",
    "communication",
}


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

        Uses hybrid evaluation: LLM for text content quality (when llm_client
        is provided), rule-based for non-text fields (boolean, integer, date, etc.).

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
        text_criteria_for_llm: List[Dict] = []

        for criterion in criteria:
            field_name = criterion['field']

            # Check conditions first — skip inapplicable criteria
            condition = criterion.get('condition')
            if condition and not self._check_condition(condition, form_state):
                section_result.criteria_results[criterion['id']] = CriterionResult(
                    criterion_id=criterion['id'],
                    field=field_name,
                    criterion=criterion['criterion'],
                    outcome='accept',
                    required=criterion.get('required', True),
                    reasoning="Criterion not applicable based on form conditions",
                    guidance=criterion.get('guidance', ''),
                )
                continue

            # Route: LLM for text fields, rule-based for everything else
            if self.llm_client and field_name in _LLM_EVALUATED_FIELDS:
                text_criteria_for_llm.append(criterion)
            else:
                criterion_result = self._evaluate_criterion(criterion, form_state)
                section_result.criteria_results[criterion['id']] = criterion_result

        # Batch LLM evaluation for text criteria
        if text_criteria_for_llm:
            llm_results = self._evaluate_text_criteria_with_llm(
                text_criteria_for_llm, form_state
            )
            section_result.criteria_results.update(llm_results)

        # Update section status and issues from all results
        for cid, cr in section_result.criteria_results.items():
            if cr.outcome == 'dont_accept':
                section_result.issues.append(cr.criterion)
                if cr.required:
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

    def _build_evaluation_prompt(
        self,
        text_criteria: List[Dict],
        form_state: Dict[str, Any],
    ) -> str:
        """Build an LLM prompt to evaluate multiple text criteria at once.
        
        Enhanced to assess quality attributes from needs assessment standards:
        - Detail and clarity of analysis
        - Evidence and source transparency
        - Prioritization and ranking
        - Root cause/driver analysis
        - Severity assessment
        - Assumptions and limitations
        - Confidence levels
        - Actionability and specificity
        """
        items = []
        for criterion in text_criteria:
            field_name = criterion["field"]
            field_value = self._get_field_value(field_name, form_state)
            items.append({
                "criterion_id": criterion["id"],
                "criterion": criterion["criterion"],
                "guidance": criterion.get("guidance", ""),
                "field_name": field_name,
                "field_value": str(field_value) if field_value else "",
            })

        prompt = (
            "You are an IFRC DREF (Disaster Relief Emergency Fund) quality evaluator.\n"
            "You assess DREF applications against quality standards for needs assessments.\n\n"
            "YOUR TASK:\n"
            "For each criterion below, check if the provided field content adequately addresses "
            "WHAT THE CRITERION IS ASKING FOR, while also meeting quality standards.\n\n"
            "CRITERION REQUIREMENT:\n"
            "- Carefully read the 'criterion' field - this defines what must be in the content\n"
            "- Read the 'guidance' field - this explains best practices\n"
            "- Check if 'field_value' actually addresses the criterion requirement\n"
            "- If criterion not met = dont_accept\n\n"
            "QUALITY STANDARDS TO ASSESS:\n"
            "1. DETAIL & CLARITY: Issues/needs are clearly and thoroughly explained\n"
            "2. EVIDENCE & SOURCES: Findings are backed by data/sources, not assumptions\n"
            "3. PRIORITIZATION: Issues are ranked or prioritized (e.g., 'most critical', 'secondary')\n"
            "4. ROOT CAUSE ANALYSIS: Underlying drivers and causes are identified, not just symptoms\n"
            "5. SEVERITY ASSESSMENT: Severity levels are explicitly stated (critical/severe/moderate/minor)\n"
            "6. ASSUMPTIONS & LIMITATIONS: Key assumptions and information gaps are acknowledged\n"
            "7. CONFIDENCE LEVELS: Uncertainty or confidence in findings is expressed\n"
            "8. ACTIONABILITY: Recommendations are specific and address identified issues\n\n"
            "DECISION RULES:\n"
            '- "accept": Field content DIRECTLY ADDRESSES THE CRITERION and demonstrates detail, '
            "evidence, and clarity\n"
            '- "dont_accept": Field content FAILS to address the criterion OR lacks detail/evidence/'
            "clarity. Missing field = dont_accept.\n"
            "- IMPORTANT: Be strict. Simple statements without depth = dont_accept.\n\n"
            "For each criterion, provide:\n"
            '- outcome: "accept" or "dont_accept"\n'
            "- reasoning: 1-2 sentences explaining whether/why the criterion is met, "
            "referencing the criterion requirement\n"
            "- improvement_suggestion: If dont_accept, specific guidance on what content to add "
            "to meet the criterion (use guidance as reference). Empty string if accept.\n\n"
            f"Criteria to evaluate:\n{json.dumps(items, indent=2)}\n\n"
            "Respond in this exact JSON format:\n"
            "{\n"
            '  "evaluations": [\n'
            "    {\n"
            '      "criterion_id": "<id>",\n'
            '      "outcome": "accept" | "dont_accept",\n'
            '      "reasoning": "...",\n'
            '      "improvement_suggestion": "..."\n'
            "    }\n"
            "  ]\n"
            "}"
        )
        return prompt

    def _evaluate_text_criteria_with_llm(
        self,
        text_criteria: List[Dict],
        form_state: Dict[str, Any],
    ) -> Dict[str, CriterionResult]:
        """Batch-evaluate text criteria using LLM. Falls back to rule-based on failure."""
        results: Dict[str, CriterionResult] = {}

        # Pre-check: skip criteria where the field is empty (no LLM call needed)
        non_empty_criteria = []
        for criterion in text_criteria:
            field_value = self._get_field_value(criterion["field"], form_state)
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                results[criterion["id"]] = CriterionResult(
                    criterion_id=criterion["id"],
                    field=criterion["field"],
                    criterion=criterion["criterion"],
                    outcome="dont_accept",
                    required=criterion.get("required", True),
                    reasoning=f"Field '{criterion['field']}' is empty",
                    improvement_prompt=self._generate_criterion_prompt(criterion, None),
                    guidance=criterion.get("guidance", ""),
                )
            else:
                non_empty_criteria.append(criterion)

        if not non_empty_criteria:
            return results

        prompt = self._build_evaluation_prompt(non_empty_criteria, form_state)

        try:
            # Retry logic with exponential backoff
            last_error = None
            for attempt in range(LLM_MAX_RETRIES):
                try:
                    response = self.llm_client.chat.completions.create(
                        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        response_format={"type": "json_object"},
                        timeout=LLM_TIMEOUT,
                    )
                    raw = json.loads(response.choices[0].message.content)
                    evaluations = {e["criterion_id"]: e for e in raw.get("evaluations", [])}
                    break  # Success, exit retry loop
                except (RateLimitError, APITimeoutError) as e:
                    last_error = e
                    if attempt < LLM_MAX_RETRIES - 1:
                        delay = LLM_RETRY_BASE_DELAY * (2 ** attempt)
                        print(f"LLM API error (attempt {attempt + 1}/{LLM_MAX_RETRIES}): {type(e).__name__}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        print(f"LLM API error after {LLM_MAX_RETRIES} attempts: {str(e)}")
                        raise last_error
            else:
                # If we get here, last attempt didn't succeed
                if last_error:
                    raise last_error
        except Exception:
            # LLM call failed — fall back to rule-based for all
            for criterion in non_empty_criteria:
                field_value = self._get_field_value(criterion["field"], form_state)
                outcome, reasoning = self._evaluate_field_value(
                    criterion["field"], field_value, criterion
                )
                improvement_prompt = ""
                if outcome == "dont_accept":
                    improvement_prompt = self._generate_criterion_prompt(criterion, field_value)
                results[criterion["id"]] = CriterionResult(
                    criterion_id=criterion["id"],
                    field=criterion["field"],
                    criterion=criterion["criterion"],
                    outcome=outcome,
                    required=criterion.get("required", True),
                    reasoning=reasoning,
                    improvement_prompt=improvement_prompt,
                    guidance=criterion.get("guidance", ""),
                )
            return results

        # Map LLM results to CriterionResult objects
        for criterion in non_empty_criteria:
            cid = criterion["id"]
            llm_eval = evaluations.get(cid)
            if llm_eval:
                outcome = llm_eval["outcome"]
                improvement_prompt = ""
                if outcome == "dont_accept":
                    improvement_prompt = self._generate_criterion_prompt(criterion, None)
                results[cid] = CriterionResult(
                    criterion_id=cid,
                    field=criterion["field"],
                    criterion=criterion["criterion"],
                    outcome=outcome,
                    required=criterion.get("required", True),
                    reasoning=llm_eval.get("reasoning", ""),
                    improvement_prompt=improvement_prompt,
                    guidance=criterion.get("guidance", ""),
                )
            else:
                # LLM didn't return this criterion — fall back to rule-based
                field_value = self._get_field_value(criterion["field"], form_state)
                outcome, reasoning = self._evaluate_field_value(
                    criterion["field"], field_value, criterion
                )
                improvement_prompt = ""
                if outcome == "dont_accept":
                    improvement_prompt = self._generate_criterion_prompt(criterion, field_value)
                results[cid] = CriterionResult(
                    criterion_id=cid,
                    field=criterion["field"],
                    criterion=criterion["criterion"],
                    outcome=outcome,
                    required=criterion.get("required", True),
                    reasoning=reasoning,
                    improvement_prompt=improvement_prompt,
                    guidance=criterion.get("guidance", ""),
                )

        return results

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
