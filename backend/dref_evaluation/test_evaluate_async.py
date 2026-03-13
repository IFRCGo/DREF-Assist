"""Tests for evaluate_async() — parallel section evaluation."""

import asyncio
import time
import pytest
from unittest.mock import Mock, patch

from dref_evaluation.evaluator import DrefEvaluator, SectionResult, EvaluationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_section_result(section_name: str, status: str = "accept") -> SectionResult:
    return SectionResult(
        section_name=section_name,
        section_display_name=section_name.replace("_", " ").title(),
        status=status,
        criteria_results={},
        issues=[],
    )


def _make_slow_evaluate_section(delay: float, status: str = "accept"):
    """Return a side_effect callable that sleeps `delay` seconds then returns a SectionResult."""
    def _fn(section_name, form_state, dref_id=0):
        time.sleep(delay)
        return _fake_section_result(section_name, status)
    return _fn


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestEvaluateAsyncStructure:
    """evaluate_async() should return the same shape as evaluate()."""

    async def test_returns_evaluation_result(self):
        evaluator = DrefEvaluator()

        with patch.object(evaluator, "evaluate_section", side_effect=_fake_section_result):
            result = await evaluator.evaluate_async(dref_id=7, form_state={})

        assert isinstance(result, EvaluationResult)
        assert result.dref_id == 7

    async def test_all_sections_present(self):
        evaluator = DrefEvaluator()
        expected_sections = set(evaluator.rubric.get_all_sections().keys())

        with patch.object(evaluator, "evaluate_section", side_effect=_fake_section_result):
            result = await evaluator.evaluate_async(dref_id=0, form_state={})

        assert set(result.section_results.keys()) == expected_sections

    async def test_pass_one_completed_flag(self):
        evaluator = DrefEvaluator()

        with patch.object(evaluator, "evaluate_section", side_effect=_fake_section_result):
            result = await evaluator.evaluate_async(dref_id=0, form_state={})

        assert result.pass_one_completed is True

    async def test_overall_status_accepted_when_all_sections_pass(self):
        evaluator = DrefEvaluator()

        with patch.object(evaluator, "evaluate_section", side_effect=_fake_section_result):
            result = await evaluator.evaluate_async(dref_id=0, form_state={})

        assert result.overall_status == "accepted"

    async def test_overall_status_needs_revision_when_any_section_fails(self):
        evaluator = DrefEvaluator()
        call_count = {"n": 0}

        def _mixed_results(section_name, form_state, dref_id=0):
            call_count["n"] += 1
            status = "needs_revision" if call_count["n"] == 1 else "accept"
            return _fake_section_result(section_name, status)

        with patch.object(evaluator, "evaluate_section", side_effect=_mixed_results):
            result = await evaluator.evaluate_async(dref_id=0, form_state={})

        assert result.overall_status == "needs_revision"

    async def test_pass_two_runs_on_needs_revision(self):
        """Pass 2 (comparative analysis) should run when overall_status is needs_revision."""
        evaluator = DrefEvaluator()

        def _failing_section(section_name, form_state, dref_id=0):
            sr = _fake_section_result(section_name, "needs_revision")
            from dref_evaluation.evaluator import CriterionResult
            sr.criteria_results["c1"] = CriterionResult(
                criterion_id="c1",
                field="event_description",
                criterion="Describe the event",
                outcome="dont_accept",
                required=True,
                reasoning="Empty field",
                guidance="Add detail",
            )
            return sr

        with patch.object(evaluator, "evaluate_section", side_effect=_failing_section):
            result = await evaluator.evaluate_async(dref_id=0, form_state={})

        assert result.pass_two_completed is True
        assert len(result.improvement_suggestions) > 0

    async def test_pass_two_skipped_when_all_accepted(self):
        evaluator = DrefEvaluator()

        with patch.object(evaluator, "evaluate_section", side_effect=_fake_section_result):
            result = await evaluator.evaluate_async(dref_id=0, form_state={})

        assert result.pass_two_completed is False


# ---------------------------------------------------------------------------
# Concurrency test
# ---------------------------------------------------------------------------

class TestEvaluateAsyncConcurrency:
    """evaluate_async() must run sections in parallel, not sequentially."""

    async def test_sections_run_concurrently(self):
        """
        Each mocked evaluate_section sleeps 0.1 s.
        Serial execution: n_sections × 0.1 s.
        Parallel execution: ≈ 0.1 s.
        We assert elapsed < half of serial time to confirm concurrency.
        """
        DELAY = 0.1
        evaluator = DrefEvaluator()
        n_sections = len(evaluator.rubric.get_all_sections())

        with patch.object(
            evaluator, "evaluate_section",
            side_effect=_make_slow_evaluate_section(DELAY),
        ):
            start = time.perf_counter()
            await evaluator.evaluate_async(dref_id=0, form_state={})
            elapsed = time.perf_counter() - start

        serial_lower_bound = n_sections * DELAY
        assert elapsed < serial_lower_bound / 2, (
            f"Took {elapsed:.2f}s for {n_sections} sections × {DELAY}s each. "
            f"Expected < {serial_lower_bound / 2:.2f}s (half of serial {serial_lower_bound:.2f}s). "
            "Sections may not be running in parallel."
        )

    async def test_evaluate_section_called_once_per_section(self):
        evaluator = DrefEvaluator()
        section_names = list(evaluator.rubric.get_all_sections().keys())
        called_with = []

        def _tracking_fn(section_name, form_state, dref_id=0):
            called_with.append(section_name)
            return _fake_section_result(section_name)

        with patch.object(evaluator, "evaluate_section", side_effect=_tracking_fn):
            await evaluator.evaluate_async(dref_id=0, form_state={})

        assert sorted(called_with) == sorted(section_names)
