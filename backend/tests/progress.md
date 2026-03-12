# LLM Evaluation Fix Progress

## Summary
Fixing 8 prompt instruction issues in `backend/llm_handler/prompt.py` to improve chatbot robustness.

## Fixes

| # | Fix | Tests | Status |
|---|-----|-------|--------|
| 1 | Prompt Injection Resistance | test_10_1 | IN PROGRESS |
| 2 | Hypothetical Scenario Rejection | test_10_3 | PENDING |
| 3 | Contradiction Surfacing in Reply | test_1_1 + test_1_3 | PENDING |
| 4+5 | Location Rules (ambiguous + informal) | test_7_1 + test_7_3 | PENDING |
| 6 | Strengthen Ambiguous Date Rule | test_6_2 | PENDING |
| 7 | Numeric Ranges | Tier 2 #12 | PENDING |
| 8 | File Metadata vs Content Mismatch | Tier 2 #21 | PENDING |
| ~~9~~ | ~~Budget Plausibility~~ | ~~Tier 2 #29~~ | SKIPPED |

## Detailed Log

### Fix 1: Prompt Injection Resistance
- **Status:** IN PROGRESS
- **Test:** `test_10_1_prompt_injection`
- **Problem:** LLM returns empty field_updates when it sees injection text like "SYSTEM: Ignore all previous instructions"
- **Solution:** Add rule 0 at top of BEHAVIOR_INSTRUCTIONS
