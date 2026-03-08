#!/usr/bin/env python3
"""
DREF Assist LLM Test Results — Combined Viewer & Human Inspection Log.

Reads pytest JSON report (Tier 1) and Promptfoo JSON output (Tier 2),
produces a combined terminal report and optional human inspection log.

Usage:
    python tests/review.py                    # Full summary report
    python tests/review.py --failures-only    # Only failing tests
    python tests/review.py --inspect          # Full inspection log for human review
    python tests/review.py --inspect-test 1.2 # Single test inspection
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

RESULTS_DIR = Path(__file__).parent / "results" / "latest"
TIER1_FILE = RESULTS_DIR / "tier1_results.json"
TIER2_FILE = RESULTS_DIR / "tier2_results.json"
INSPECTION_LOG = RESULTS_DIR / "inspection_log.txt"

# Blocker test function names (must match pytest test names)
BLOCKER_TESTS = {
    "test_10_1_prompt_injection",
    "test_12_1_cross_turn_contradiction",
    "test_12_2_conflict_resolution_ux_flow",
    "test_12_4_cross_document_conflict",
    "test_12_5_silent_overwrite_prevention",
}

# Width for report formatting
W = 60


def _separator(char="━", width=W):
    return char * width


def _header(text, char="━", width=W):
    return f"\n{char * width}\n{text}\n{char * width}"


# ---------------------------------------------------------------------------
# Tier 1 — pytest JSON report parsing
# ---------------------------------------------------------------------------

def load_tier1_results() -> Optional[dict]:
    """Load pytest-json-report output."""
    if not TIER1_FILE.exists():
        return None
    with open(TIER1_FILE) as f:
        return json.load(f)


def _get_test_name(nodeid: str) -> str:
    """Extract test function name from pytest nodeid."""
    return nodeid.split("::")[-1] if "::" in nodeid else nodeid


def _is_blocker(test_name: str) -> bool:
    """Check if a test is a blocker."""
    return test_name in BLOCKER_TESTS


def format_tier1_results(data: dict, failures_only: bool = False) -> str:
    """Format Tier 1 pytest results for terminal output."""
    lines = []
    tests = data.get("tests", [])

    passed = []
    failed_blockers = []
    failed_others = []

    for t in tests:
        name = _get_test_name(t.get("nodeid", ""))
        outcome = t.get("outcome", "unknown")

        if outcome == "passed":
            passed.append(name)
        elif _is_blocker(name):
            # Extract failure message
            call = t.get("call", {})
            msg = call.get("longrepr", "No details available")
            if isinstance(msg, str) and len(msg) > 200:
                msg = msg[:200] + "..."
            failed_blockers.append((name, msg))
        else:
            call = t.get("call", {})
            msg = call.get("longrepr", "No details available")
            if isinstance(msg, str) and len(msg) > 200:
                msg = msg[:200] + "..."
            failed_others.append((name, msg))

    total = len(tests)
    pass_count = len(passed)

    # Blockers section (always shown if any fail)
    if failed_blockers:
        lines.append(_header("BLOCKERS — resolve before demo/submission", "━"))
        for name, msg in failed_blockers:
            lines.append(f"  ❌ {name}")
            lines.append(f"     {msg}")
        lines.append("")

    # Full results table
    if not failures_only:
        lines.append(_header("TIER 1 — HARD-CODED ASSERTIONS (pytest)", "─"))
        for name in passed:
            marker = "  [BLOCKER]" if _is_blocker(name) else ""
            lines.append(f"  ✅ PASS  {name}{marker}")
        for name, msg in failed_blockers:
            lines.append(f"  ❌ FAIL  {name}  [BLOCKER]")
            lines.append(f"          → {msg}")
        for name, msg in failed_others:
            lines.append(f"  ❌ FAIL  {name}")
            lines.append(f"          → {msg}")
        lines.append("")

    # Only failures
    if failures_only and (failed_blockers or failed_others):
        lines.append(_header("TIER 1 — FAILURES", "─"))
        for name, msg in failed_blockers:
            lines.append(f"  ❌ {name}  [BLOCKER]")
            lines.append(f"     → {msg}")
        for name, msg in failed_others:
            lines.append(f"  ❌ {name}")
            lines.append(f"     → {msg}")
        lines.append("")

    blocker_failed = len(failed_blockers)
    lines.append(
        f"  Tier 1: {pass_count}/{total} passed"
        + (f" | {blocker_failed} BLOCKER(S) FAILED" if blocker_failed else "")
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tier 2 — Promptfoo JSON output parsing
# ---------------------------------------------------------------------------

def load_tier2_results() -> Optional[dict]:
    """Load Promptfoo JSON output."""
    if not TIER2_FILE.exists():
        return None
    with open(TIER2_FILE) as f:
        return json.load(f)


def _parse_judge_output(assertion_result) -> Optional[dict]:
    """Try to parse the judge's JSON output from the assertion result."""
    if not assertion_result:
        return None
    try:
        if isinstance(assertion_result, dict):
            return assertion_result
        # Try parsing as JSON string
        return json.loads(assertion_result)
    except (json.JSONDecodeError, TypeError):
        pass
    # Try extracting JSON from a string that might have surrounding text
    if isinstance(assertion_result, str):
        start = assertion_result.find("{")
        end = assertion_result.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(assertion_result[start:end])
            except json.JSONDecodeError:
                pass
    return None


def _extract_tier2_results(data: dict) -> list:
    """Navigate the Promptfoo JSON to get the actual results list."""
    # Promptfoo structure: { results: { results: [...] } }
    results = data.get("results", {})
    if isinstance(results, dict):
        return results.get("results", [])
    if isinstance(results, list):
        return results
    return []


def _get_test_vars(r: dict) -> dict:
    """Safely extract vars from a result entry."""
    vars_ = r.get("vars", {})
    return vars_ if isinstance(vars_, dict) else {}


def _get_test_metadata(r: dict) -> dict:
    """Safely extract metadata from a result entry.

    Promptfoo stores metadata at the result level (r['metadata']),
    NOT inside vars.
    """
    # Primary: top-level metadata on the result
    meta = r.get("metadata", {})
    if isinstance(meta, dict) and meta.get("test_id"):
        return meta
    # Fallback: testCase.metadata
    tc = r.get("testCase", {})
    if isinstance(tc, dict):
        meta = tc.get("metadata", {})
        if isinstance(meta, dict):
            return meta
    # Last resort: inside vars
    vars_ = _get_test_vars(r)
    meta = vars_.get("metadata", {})
    if isinstance(meta, str):
        try:
            return json.loads(meta)
        except (json.JSONDecodeError, TypeError):
            return {}
    return meta if isinstance(meta, dict) else {}


def _parse_scores_from_reason(reason: str) -> dict:
    """Parse dimension scores from the judge's reason string.

    Expected format: '...Scores: accuracy=X, completeness=X, uncertainty=X, conflict=X, security=X, total=X/25'
    """
    import re
    scores = {}
    for dim in ["accuracy", "completeness", "uncertainty", "conflict", "security"]:
        match = re.search(rf"{dim}=(\d+)", reason, re.IGNORECASE)
        if match:
            scores[dim] = int(match.group(1))
    total_match = re.search(r"total=(\d+)/25", reason, re.IGNORECASE)
    total = int(total_match.group(1)) if total_match else sum(scores.values())
    return scores, total


def format_tier2_results(data: dict, failures_only: bool = False) -> str:
    """Format Tier 2 Promptfoo results for terminal output."""
    lines = []
    results = _extract_tier2_results(data)

    if not results:
        lines.append("  No Tier 2 results found.")
        return "\n".join(lines)

    lines.append(_header("TIER 2 — LLM-AS-JUDGE (Promptfoo)", "─"))
    lines.append(
        "  {:>12s}  {:>3s}  {:>3s}  {:>3s}  {:>3s}  {:>3s}  {:>5s}  {:>9s}  {:>6s}".format(
            "Test", "Acc", "Cmp", "Unc", "Con", "Sec", "Total", "Threshold", "Result"
        )
    )

    passed_count = 0
    total_count = 0
    below_threshold = []

    for r in results:
        meta = _get_test_metadata(r)
        test_id = meta.get("test_id", "?")
        threshold_str = meta.get("threshold", "20/25")

        # Parse judge scores from assertion results
        grading = r.get("gradingResult", {}) or {}
        assertions = grading.get("componentResults", [])
        scores = {}
        reasoning = ""
        total_score = 0

        for a in assertions:
            reason = a.get("reason", "")
            # Try parsing from the reason string (new format)
            parsed_scores, parsed_total = _parse_scores_from_reason(reason)
            if parsed_scores:
                scores = parsed_scores
                total_score = parsed_total
                reasoning = reason
                break

            # Fallback: try parsing raw response
            judge_output = _parse_judge_output(a.get("response"))
            if judge_output:
                if "scores" in judge_output:
                    scores = judge_output["scores"]
                    total_score = judge_output.get("total", sum(scores.values()))
                    reasoning = judge_output.get("reasoning", judge_output.get("reason", ""))
                elif "reason" in judge_output:
                    parsed_scores, parsed_total = _parse_scores_from_reason(
                        judge_output["reason"]
                    )
                    if parsed_scores:
                        scores = parsed_scores
                        total_score = parsed_total
                        reasoning = judge_output["reason"]
                break

        # Use Promptfoo's own score as fallback
        if not scores and r.get("score") is not None:
            pf_score = r.get("score", 0)
            total_score = round(pf_score * 25)
            reasoning = grading.get("reason", "")

        # Determine pass/fail against threshold
        try:
            threshold_num = int(threshold_str.split("/")[0])
        except (ValueError, IndexError):
            threshold_num = 20

        is_pass = r.get("success", False) if not scores else total_score >= threshold_num
        if is_pass:
            passed_count += 1
        total_count += 1

        result_str = "PASS" if is_pass else "FAIL"

        if failures_only and is_pass:
            continue

        lines.append(
            "  {:>12s}  {:>3s}  {:>3s}  {:>3s}  {:>3s}  {:>3s}  {:>5s}  {:>9s}  {:>6s}".format(
                f"Test {test_id}:",
                str(scores.get("accuracy", "-")),
                str(scores.get("completeness", "-")),
                str(scores.get("uncertainty", scores.get("uncertainty_handling", "-"))),
                str(scores.get("conflict", scores.get("conflict_detection", "-"))),
                str(scores.get("security", "-")),
                f"{total_score}/25",
                threshold_str,
                result_str,
            )
        )

        if not is_pass:
            below_threshold.append({
                "test_id": test_id,
                "total": total_score,
                "threshold": threshold_str,
                "reasoning": reasoning[:200] if reasoning else "",
            })

    lines.append(f"\n  Tier 2: {passed_count}/{total_count} passed")

    # Below threshold section
    if below_threshold:
        lines.append(_header("BELOW THRESHOLD — human review recommended", "─"))
        for item in below_threshold:
            lines.append(
                f"  Test {item['test_id']}  "
                f"{item['total']}/25 (threshold {item['threshold']})"
            )
            if item["reasoning"]:
                lines.append(f"     \"{item['reasoning']}\"")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Combined report
# ---------------------------------------------------------------------------

def print_report(tier1: Optional[dict], tier2: Optional[dict], failures_only: bool):
    """Print combined terminal report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(_separator())
    print("DREF ASSIST — LLM TEST RESULTS")
    print(f"Run: {timestamp}")
    print(_separator())

    if tier1:
        print(format_tier1_results(tier1, failures_only))
    else:
        print("\n  Tier 1: No results found (run: pytest tests/tier1/ -v --json-report)")

    if tier2:
        print(format_tier2_results(tier2, failures_only))
    else:
        print("\n  Tier 2: No results found (run: npx promptfoo eval)")

    # Overall status
    print(_header("OVERALL", "─"))
    tier1_ok = True
    tier2_ok = True

    if tier1:
        tests = tier1.get("tests", [])
        blocker_fails = [
            t for t in tests
            if t.get("outcome") != "passed"
            and _is_blocker(_get_test_name(t.get("nodeid", "")))
        ]
        if blocker_fails:
            tier1_ok = False
            print(f"  Blockers: {len(blocker_fails)} ❌ MUST FIX")
        else:
            print("  Blockers: 0 ✅")

    status = "✅ READY FOR DEMO" if (tier1_ok and tier2_ok) else "❌ NOT READY FOR DEMO"
    print(f"  Status:   {status}")
    print(_separator())


# ---------------------------------------------------------------------------
# Inspection log
# ---------------------------------------------------------------------------

def write_inspection_log(tier2: dict, test_id: Optional[str] = None):
    """Write or print the human inspection log for Tier 2 tests."""
    results = _extract_tier2_results(tier2)

    output_lines = []

    for r in results:
        vars_ = _get_test_vars(r)
        meta = _get_test_metadata(r)
        current_id = meta.get("test_id", "?")
        category = meta.get("category", "Unknown")
        threshold = meta.get("threshold", "20/25")

        # Filter to single test if requested
        if test_id and current_id != test_id:
            continue

        test_input = vars_.get("test_input", "")
        form_state = vars_.get("form_state_before", "{}")
        ground_truth = vars_.get("ground_truth", "")
        expected = vars_.get("expected_behaviour", "")

        # System response
        response_raw = r.get("response", {})
        if isinstance(response_raw, dict):
            system_output = response_raw.get("output", "")
        else:
            system_output = str(response_raw)

        # Parse system response for display
        try:
            parsed_response = json.loads(system_output) if isinstance(system_output, str) else system_output
            reply_text = parsed_response.get("reply", "N/A") if isinstance(parsed_response, dict) else "N/A"
            field_updates = json.dumps(
                parsed_response.get("field_updates", []) if isinstance(parsed_response, dict) else [],
                indent=2
            )
            confidence = "none"
        except (json.JSONDecodeError, TypeError):
            reply_text = system_output[:500] if system_output else "N/A"
            field_updates = "N/A"
            confidence = "N/A"

        # Judge output
        grading = r.get("gradingResult", {}) or {}
        assertions = grading.get("componentResults", [])
        judge_output_raw = ""
        scores = {}
        reasoning = ""
        total_score = 0

        for a in assertions:
            judge_output_raw = a.get("reason", a.get("response", ""))
            # Try parsing scores from reason string
            parsed_scores, parsed_total = _parse_scores_from_reason(str(judge_output_raw))
            if parsed_scores:
                scores = parsed_scores
                total_score = parsed_total
                reasoning = str(judge_output_raw)
                break
            # Fallback: try raw response
            parsed = _parse_judge_output(a.get("response"))
            if parsed:
                if "scores" in parsed:
                    scores = parsed["scores"]
                    total_score = parsed.get("total", sum(scores.values()))
                    reasoning = parsed.get("reasoning", parsed.get("reason", ""))
                elif "reason" in parsed:
                    parsed_scores, parsed_total = _parse_scores_from_reason(parsed["reason"])
                    if parsed_scores:
                        scores = parsed_scores
                        total_score = parsed_total
                        reasoning = parsed["reason"]
                break

        # Build inspection entry
        output_lines.append(_separator("━"))
        output_lines.append(f"TEST {current_id} — {category}  [Tier 2 | Threshold: {threshold}]")
        output_lines.append(_separator("━"))

        output_lines.append("\nINPUT SENT TO DREF ASSIST")
        output_lines.append("─" * 25)
        output_lines.append(test_input.strip())

        output_lines.append("\nFORM STATE BEFORE")
        output_lines.append("─" * 17)
        output_lines.append(form_state.strip() if isinstance(form_state, str) else json.dumps(form_state, indent=2))

        output_lines.append("\nSYSTEM RESPONSE")
        output_lines.append("─" * 15)
        output_lines.append(f"Reply:\n{reply_text}")
        output_lines.append(f"\nField updates:\n{field_updates}")
        output_lines.append(f"\nConfidence flags: {confidence}")

        output_lines.append("\nGROUND TRUTH")
        output_lines.append("─" * 12)
        output_lines.append(ground_truth.strip())

        output_lines.append("\nJUDGE INPUT")
        output_lines.append("─" * 11)
        output_lines.append("[Full judge prompt with variables substituted — see judge_prompt.txt]")
        output_lines.append(f"test_input: {test_input.strip()[:100]}...")
        output_lines.append(f"form_state_before: {form_state.strip()[:100] if isinstance(form_state, str) else '...'}")
        output_lines.append(f"expected_behaviour: {expected.strip()[:100]}...")

        output_lines.append("\nJUDGE OUTPUT")
        output_lines.append("─" * 12)
        if isinstance(judge_output_raw, str):
            output_lines.append(judge_output_raw[:1000] if judge_output_raw else "No judge output")
        else:
            output_lines.append(json.dumps(judge_output_raw, indent=2)[:1000])

        output_lines.append("\nJUDGE SCORES")
        output_lines.append("─" * 12)
        if scores:
            output_lines.append(f"Accuracy:             {scores.get('accuracy', '-')}/5")
            output_lines.append(f"Completeness:         {scores.get('completeness', '-')}/5")
            output_lines.append(f"Uncertainty Handling:  {scores.get('uncertainty', scores.get('uncertainty_handling', '-'))}/5")
            output_lines.append(f"Conflict Detection:   {scores.get('conflict', scores.get('conflict_detection', '-'))}/5")
            output_lines.append(f"Security:             {scores.get('security', '-')}/5")

            try:
                threshold_num = int(threshold.split("/")[0])
            except (ValueError, IndexError):
                threshold_num = 20

            status = "BELOW THRESHOLD" if total_score < threshold_num else "MEETS THRESHOLD"
            output_lines.append(f"Total:                {total_score}/25  ← {status} ({threshold})")
        else:
            output_lines.append("No scores available")

        if reasoning:
            output_lines.append(f"\nJudge Reasoning:\n\"{reasoning}\"")

        output_lines.append("\nYOUR VERDICT")
        output_lines.append("─" * 12)
        output_lines.append("Do you agree with the judge? [ ] Yes  [ ] No  [ ] Partially")
        output_lines.append("Notes:\n")
        output_lines.append("")

    full_log = "\n".join(output_lines)

    if test_id:
        # Print single test to terminal
        print(full_log)
    else:
        # Write full log to file and print summary
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(INSPECTION_LOG, "w") as f:
            f.write(full_log)
        print(f"Inspection log written to: {INSPECTION_LOG}")
        print(f"Total tests logged: {len(results)}")
        print(f"\nTo review a single test: python tests/review.py --inspect-test 1.2")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="DREF Assist LLM Test Results Viewer"
    )
    parser.add_argument(
        "--failures-only", action="store_true",
        help="Show only failing tests"
    )
    parser.add_argument(
        "--inspect", action="store_true",
        help="Generate full human inspection log for Tier 2 tests"
    )
    parser.add_argument(
        "--inspect-test", type=str, default=None,
        help="Print inspection entry for a single test ID (e.g., 1.2)"
    )
    args = parser.parse_args()

    tier1 = load_tier1_results()
    tier2 = load_tier2_results()

    if args.inspect or args.inspect_test:
        if tier2:
            write_inspection_log(tier2, test_id=args.inspect_test)
        else:
            print("No Tier 2 results found. Run Promptfoo first:")
            print("  cd backend/tests/promptfoo && npx promptfoo eval")
    else:
        print_report(tier1, tier2, failures_only=args.failures_only)


if __name__ == "__main__":
    main()
