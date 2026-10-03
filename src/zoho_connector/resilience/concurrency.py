"""
Concurrency limiter using asyncio Semaphore.
Restricts the maximum number of simultaneous HTTP connections to Zoho API.
"""

import asyncio
from types import TracebackType
from typing import Optional, Type


class AsyncConcurrencyLimiter:
    """Limits concurrent asynchronous operations using an asyncio Semaphore."""

    def __init__(self, max_concurrent: int = 5):
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than 0")
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        """Current number of active operations."""
        return self._active_count

    async def __aenter__(self) -> "AsyncConcurrencyLimiter":
        await self._semaphore.acquire()
        async with self._lock:
            self._active_count += 1
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        try:
            async with self._lock:
                self._active_count = max(0, self._active_count - 1)
        finally:
            self._semaphore.release()
