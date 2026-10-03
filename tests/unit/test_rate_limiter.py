"""
Unit tests for AsyncTokenBucketRateLimiter.
"""

import asyncio
import time
import pytest

from zoho_connector.resilience.rate_limiter import AsyncTokenBucketRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_immediate_acquisition():
    """Initial acquisitions within capacity should not sleep."""
    limiter = AsyncTokenBucketRateLimiter(requests_per_minute=60, burst_capacity=5)
    waited = await limiter.acquire()
    assert waited == 0.0
    assert limiter.tokens == 4.0


@pytest.mark.asyncio
async def test_rate_limiter_throttling():
    """When tokens are exhausted, acquire should wait for token replenishment."""
    # 600 req/min = 10 req/sec = 0.1s per token
    limiter = AsyncTokenBucketRateLimiter(requests_per_minute=600, burst_capacity=1)
    
    # First token immediate
    w1 = await limiter.acquire()
    assert w1 == 0.0

    # Second token requires wait of ~0.1s
    start = time.monotonic()
    w2 = await limiter.acquire()
    elapsed = time.monotonic() - start

    assert w2 > 0.0
    assert elapsed >= 0.08


def test_rate_limiter_invalid_config():
    """Rate limiter should reject negative or zero rate."""
    with pytest.raises(ValueError):
        AsyncTokenBucketRateLimiter(requests_per_minute=0)


def test_rate_limiter_reset():
    """Reset restores full token capacity."""
    limiter = AsyncTokenBucketRateLimiter(requests_per_minute=60, burst_capacity=10)
    limiter.tokens = 0.0
    limiter.reset()
    assert limiter.tokens == 10.0
