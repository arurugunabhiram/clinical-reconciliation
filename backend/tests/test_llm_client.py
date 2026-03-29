"""Unit tests for llm/client.py — retry logic and error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import anthropic

from llm.client import AIServiceError, llm_reconcile
from schemas.reconcile import MedicationSource


def _make_rate_limit_error() -> anthropic.RateLimitError:
    """Construct a RateLimitError with a minimal mock httpx response."""
    mock_response = MagicMock()
    mock_response.request = MagicMock()
    return anthropic.RateLimitError("Rate limited", response=mock_response, body=None)


_SOURCES = [
    MedicationSource(system="Hospital", medication="Aspirin 81mg", source_reliability="high"),
    MedicationSource(system="Clinic", medication="Aspirin 325mg", source_reliability="high"),
]

_VALID_JSON = (
    '{"reconciled_medication": "Aspirin 81mg daily", "confidence_score": 0.8, '
    '"reasoning": "Test reasoning.", "recommended_actions": ["Check with doctor"], '
    '"clinical_safety_check": "PASSED"}'
)


# ---------------------------------------------------------------------------
# Test A — 429 retry logic: succeeds after two rate-limit errors
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_retry_on_rate_limit_then_succeeds(monkeypatch):
    """LLM call retries on RateLimitError and returns result on third attempt."""
    call_count = 0

    async def mock_create(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise _make_rate_limit_error()
        mock_response = AsyncMock()
        mock_response.content = [AsyncMock(text=_VALID_JSON)]
        return mock_response

    mock_client = AsyncMock()
    mock_client.messages.create = mock_create

    with patch("llm.client._get_client", return_value=mock_client):
        with patch("llm.client.asyncio.sleep", new_callable=AsyncMock):
            monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
            result = await llm_reconcile(_SOURCES, None)

    assert result.reconciled_medication == "Aspirin 81mg daily"
    assert call_count == 3


# ---------------------------------------------------------------------------
# Test B — All retries exhausted → AIServiceError raised
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_raises_ai_service_error_after_max_retries(monkeypatch):
    """AIServiceError is raised when all retry attempts hit rate limit."""

    async def always_rate_limit(*args, **kwargs):
        raise _make_rate_limit_error()

    mock_client = AsyncMock()
    mock_client.messages.create = always_rate_limit

    with patch("llm.client._get_client", return_value=mock_client):
        with patch("llm.client.asyncio.sleep", new_callable=AsyncMock):
            monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
            with pytest.raises(AIServiceError):
                await llm_reconcile(_SOURCES, None)
