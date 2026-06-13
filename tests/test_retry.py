"""
tests.test_retry - Unit tests for vulguard.retry.

:author: Ron Webb
:since: 1.0.0
"""

from unittest.mock import AsyncMock, patch

import pytest

from vulguard.retry import _compute_delay, retry_async


class TestComputeDelay:
    """Tests for the _compute_delay helper.

    :author: Ron Webb
    :since: 1.0.0
    """

    def test_delay_within_bounds(self) -> None:
        """_compute_delay() always returns a value between 0 and max_delay."""
        for attempt in range(10):
            delay = _compute_delay(attempt, base_delay=0.5, max_delay=10.0)
            assert 0.0 <= delay <= 10.0

    def test_delay_respects_max_delay_cap(self) -> None:
        """_compute_delay() never exceeds max_delay regardless of attempt number."""
        for attempt in range(20):
            delay = _compute_delay(attempt, base_delay=1.0, max_delay=2.0)
            assert delay <= 2.0

    def test_zero_base_delay_always_returns_zero(self) -> None:
        """_compute_delay() returns 0 when base_delay is 0."""
        delay = _compute_delay(3, base_delay=0.0, max_delay=10.0)
        assert delay == 0.0


class TestRetryAsync:
    """Tests for the retry_async helper.

    :author: Ron Webb
    :since: 1.0.0
    """

    async def test_succeeds_on_first_attempt(self) -> None:
        """retry_async() returns the result immediately when the first call succeeds."""
        func = AsyncMock(return_value="ok")
        result = await retry_async(func, max_attempts=3, base_delay=0.0, max_delay=0.0)
        assert result == "ok"
        assert func.call_count == 1

    async def test_retries_on_transient_failure(self) -> None:
        """retry_async() retries after a transient exception and returns the success."""
        func = AsyncMock(side_effect=[RuntimeError("transient"), "recovered"])
        with patch("vulguard.retry.asyncio.sleep", new=AsyncMock()):
            result = await retry_async(
                func, max_attempts=3, base_delay=0.0, max_delay=0.0
            )
        assert result == "recovered"
        assert func.call_count == 2

    async def test_raises_after_all_attempts_exhausted(self) -> None:
        """retry_async() re-raises the last exception when all attempts fail."""
        func = AsyncMock(side_effect=ValueError("permanent"))
        with patch("vulguard.retry.asyncio.sleep", new=AsyncMock()):
            with pytest.raises(ValueError, match="permanent"):
                await retry_async(func, max_attempts=3, base_delay=0.0, max_delay=0.0)
        assert func.call_count == 3

    async def test_exact_attempt_count_on_mixed_failures(self) -> None:
        """retry_async() stops as soon as a call succeeds."""
        func = AsyncMock(side_effect=[RuntimeError("e1"), RuntimeError("e2"), "done"])
        with patch("vulguard.retry.asyncio.sleep", new=AsyncMock()):
            result = await retry_async(
                func, max_attempts=5, base_delay=0.0, max_delay=0.0
            )
        assert result == "done"
        assert func.call_count == 3

    async def test_args_and_kwargs_forwarded(self) -> None:
        """retry_async() forwards positional and keyword arguments to the function."""

        async def _echo(pos: str, *, kw: str) -> str:
            return f"{pos}-{kw}"

        result = await retry_async(
            _echo, "hello", kw="world", max_attempts=1, base_delay=0.0, max_delay=0.0
        )
        assert result == "hello-world"
