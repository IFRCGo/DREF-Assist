# LLM Evaluation Fix Progress

## Summary
Fixing 8 prompt instruction issues in `backend/llm_handler/prompt.py` to improve chatbot robustness.

## IMPORTANT: Never use test data in prompts
When adding rules/examples to BEHAVIOR_INSTRUCTIONS, NEVER use inputs from the test suite.
This would cause overfitting — the LLM memorizes the test case rather than learning the rule,
making the tests meaningless.

## Fixes

| # | Fix | Tests | Status |
|---|-----|-------|--------|
| 1 | Prompt Injection Resistance | test_10_1 | DONE (test updated + prompt rule added) |
| 2 | Hypothetical Scenario Rejection | test_10_3 | IN PROGRESS |
| 3 | Contradiction Surfacing in Reply | test_1_1 + test_1_3 | PENDING |
| 4+5 | Location Rules (ambiguous + informal) | test_7_1 + test_7_3 | PENDING |
| 6 | Strengthen Ambiguous Date Rule | test_6_2 | PENDING |
| 7 | Numeric Ranges | Tier 2 #12 | PENDING |
| 8 | File Metadata vs Content Mismatch | Tier 2 #21 | PENDING |
| ~~9~~ | ~~Budget Plausibility~~ | ~~Tier 2 #29~~ | SKIPPED |

## Detailed Log

### Fix 1: Prompt Injection Resistance — DONE
- **Test:** `test_10_1_prompt_injection`
- **Problem:** Azure content filter rejects messages with injection text before GPT-4o sees them
- **Solution:** Updated test to accept both outcomes (Azure rejection OR LLM extraction). Added prompt rule 0 as defense-in-depth.
- **Commit:** 116d5e1

### Fix 2: Hypothetical Scenario Rejection — IN PROGRESS
- **Test:** `test_10_3_hypothetical_scenario`
- **Problem:** LLM extracts field_updates from hypothetical/conditional messages ("If...", "preparedness exercise")
- **Solution:** Added HYPOTHETICAL/CONDITIONAL classification sub-rule
