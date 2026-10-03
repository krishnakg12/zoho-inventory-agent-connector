"""
Token bucket rate limiter for proactive client-side throttling.
Prevents upstream Zoho HTTP 429 errors by maintaining safety headroom.
"""

import asyncio
import time
from typing import Optional


class AsyncTokenBucketRateLimiter:
    """
    Asynchronous token bucket rate limiter.
    Ensures outbound request rate does not exceed the configured requests per minute.
    """

    def __init__(self, requests_per_minute: int = 60, burst_capacity: Optional[int] = None):
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be greater than 0")
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.capacity = float(burst_capacity if burst_capacity is not None else requests_per_minute)
        self.tokens = self.capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> float:
        """
        Acquire 1 token. If no tokens are available, sleep until a token is refilled.
        Returns the duration waited in seconds.
        """
        waited = 0.0
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.last_refill = now

                # Add tokens based on elapsed time
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return waited

                # Calculate wait time needed for at least 1 full token
                needed = 1.0 - self.tokens
                wait_time = needed / self.rate

            # Sleep outside the lock so other tasks aren't blocked from checking
            await asyncio.sleep(wait_time)
            waited += wait_time

    def reset(self) -> None:
        """Reset the bucket to full capacity (useful for tests)."""
        self.tokens = self.capacity
        self.last_refill = time.monotonic()
