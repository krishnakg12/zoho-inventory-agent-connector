"""
Unit tests for AsyncConcurrencyLimiter.
"""

import asyncio
import pytest

from zoho_connector.resilience.concurrency import AsyncConcurrencyLimiter


@pytest.mark.asyncio
async def test_concurrency_limiter_bounds_execution():
    """Verify that no more than max_concurrent tasks run concurrently."""
    limiter = AsyncConcurrencyLimiter(max_concurrent=3)
    current_active = 0
    max_observed_active = 0

    async def worker():
        nonlocal current_active, max_observed_active
        async with limiter:
            current_active += 1
            max_observed_active = max(max_observed_active, current_active)
            await asyncio.sleep(0.05)
            current_active -= 1

    tasks = [worker() for _ in range(10)]
    await asyncio.gather(*tasks)

    assert max_observed_active <= 3
    assert limiter.active_count == 0


@pytest.mark.asyncio
async def test_concurrency_limiter_handles_exception():
    """Verify that lock is properly released if an exception occurs inside context."""
    limiter = AsyncConcurrencyLimiter(max_concurrent=2)

    with pytest.raises(RuntimeError):
        async with limiter:
            assert limiter.active_count == 1
            raise RuntimeError("Task failed")

    assert limiter.active_count == 0


def test_concurrency_limiter_invalid():
    with pytest.raises(ValueError):
        AsyncConcurrencyLimiter(max_concurrent=0)
