"""Tests for /api/evaluate caching and cache-key helpers in app.py."""

import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

import app as app_module
from app import app, _eval_cache_key, _CACHE_TTL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FORM_STATE_A = {
    "operation_overview.country": "Kenya",
    "event_detail.what_happened": "Flooding in the northern region",
}

FORM_STATE_B = {
    "operation_overview.country": "Ethiopia",
    "event_detail.what_happened": "Drought affecting southern districts",
}

FAKE_EVAL_RESULT = {
    "overall_status": "accepted",
    "section_results": {},
    "improvement_suggestions": [],
    "pass_one_completed": True,
    "pass_two_completed": False,
    "reference_examples_used": [],
    "dref_id": 0,
}


def _patch_evaluator(return_value=None):
    """Patch DrefEvaluator so evaluate_async returns immediately without LLM calls."""
    mock_result = MagicMock()
    mock_evaluator_instance = MagicMock()
    mock_evaluator_instance.evaluate_async = AsyncMock(return_value=mock_result)
    mock_evaluator_instance.to_dict.return_value = return_value or FAKE_EVAL_RESULT
    return patch("app.DrefEvaluator", return_value=mock_evaluator_instance), mock_evaluator_instance


# ---------------------------------------------------------------------------
# Cache key tests  (pure-function, no HTTP needed)
# ---------------------------------------------------------------------------

class TestEvalCacheKey:
    def test_same_dict_produces_same_key(self):
        assert _eval_cache_key(FORM_STATE_A) == _eval_cache_key(FORM_STATE_A)

    def test_key_is_order_independent(self):
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert _eval_cache_key(d1) == _eval_cache_key(d2)

    def test_different_dicts_produce_different_keys(self):
        assert _eval_cache_key(FORM_STATE_A) != _eval_cache_key(FORM_STATE_B)

    def test_nested_dict_stable(self):
        d = {"section": {"z": 3, "a": 1}, "top": "val"}
        assert _eval_cache_key(d) == _eval_cache_key(d)

    def test_returns_64_char_hex_string(self):
        key = _eval_cache_key(FORM_STATE_A)
        assert isinstance(key, str)
        assert len(key) == 64  # SHA-256 hex digest


# ---------------------------------------------------------------------------
# Endpoint cache behaviour
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_cache():
    """Wipe the module-level cache dict before and after every test."""
    app_module._eval_cache.clear()
    yield
    app_module._eval_cache.clear()


async def test_cache_miss_calls_evaluator():
    """First request triggers evaluate_async."""
    ctx, mock_ev = _patch_evaluator()
    with ctx:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})

    assert resp.status_code == 200
    mock_ev.evaluate_async.assert_awaited_once()


async def test_cache_hit_skips_evaluator():
    """Second identical request returns cached result without calling evaluate_async."""
    ctx, mock_ev = _patch_evaluator()
    with ctx:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})
            await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})

    assert mock_ev.evaluate_async.await_count == 1


async def test_cache_hit_returns_same_payload():
    """Cached response body is identical to the original response."""
    ctx, mock_ev = _patch_evaluator()
    with ctx:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r1 = await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})
            r2 = await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})

    assert r1.json() == r2.json()


async def test_different_form_state_is_cache_miss():
    """Different form state must bypass cache and trigger a new evaluation."""
    ctx, mock_ev = _patch_evaluator()
    with ctx:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})
            await client.post("/api/evaluate", json={"form_state": FORM_STATE_B})

    assert mock_ev.evaluate_async.await_count == 2


async def test_expired_cache_entry_triggers_new_evaluation():
    """After TTL elapses the cache entry is ignored and the evaluator is called again."""
    ctx, mock_ev = _patch_evaluator()
    with ctx:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})

            # Manually expire the cache entry
            key = _eval_cache_key(
                app_module._map_frontend_to_rubric(
                    app_module._extract_plain_values(FORM_STATE_A)
                )
            )
            result_dict, _ = app_module._eval_cache[key]
            app_module._eval_cache[key] = (result_dict, time.monotonic() - _CACHE_TTL - 1)

            await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})

    assert mock_ev.evaluate_async.await_count == 2


async def test_fresh_cache_entry_not_expired():
    """An entry 1 second old is still within TTL and must be a cache hit."""
    ctx, mock_ev = _patch_evaluator()
    with ctx:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})

            key = _eval_cache_key(
                app_module._map_frontend_to_rubric(
                    app_module._extract_plain_values(FORM_STATE_A)
                )
            )
            result_dict, _ = app_module._eval_cache[key]
            app_module._eval_cache[key] = (result_dict, time.monotonic() - 1)

            await client.post("/api/evaluate", json={"form_state": FORM_STATE_A})

    assert mock_ev.evaluate_async.await_count == 1
