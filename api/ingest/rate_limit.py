"""Token-bucket rate limiter for SEC EDGAR.

PRD 6.1: SEC rate-limits to 10 requests/second and we pace at 8 to leave
headroom. PRD 16 lists an IP block as low-likelihood / high-impact -- it costs
days, and no other component in this project can fail that expensively. The
limiter is built before the client that uses it, and every EDGAR call goes
through the one shared instance.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

# Requests per second. Under SEC's documented 10/s ceiling.
EDGAR_RATE_LIMIT = 8.0


class RateLimiter:
    """Paces callers to at most `rate` acquisitions per second.

    A token bucket refilling continuously at `rate` tokens/sec. `capacity` is the
    burst allowance and defaults to 1, meaning strict pacing: consecutive
    acquires are separated by at least 1/rate seconds, so no more than `rate`
    requests can leave in any one-second window. A larger capacity permits a
    burst of saved-up credit after an idle period, which SEC's ceiling would
    tolerate but which buys nothing here -- ingestion is not latency-sensitive.

    The bucket starts EMPTY rather than full, so even the first call pays one
    interval. A fresh process has no way to know whether a previous run just
    finished hammering EDGAR; 125ms at startup is cheap insurance against
    resuming an interrupted ingest straight into a burst.

    `clock` and `sleep` are injectable so the pacing logic can be tested
    deterministically without spending real wall-clock time.

    Thread-safe. The lock is deliberately held across the sleep: this serializes
    callers so requests leave one at a time, correctly paced. That is the
    intended behavior for a shared limiter guarding a single external service,
    not an oversight.
    """

    def __init__(
        self,
        rate: float = EDGAR_RATE_LIMIT,
        capacity: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate <= 0:
            raise ValueError(f"rate must be positive, got {rate}")
        if capacity < 1:
            raise ValueError(f"capacity must be at least 1, got {capacity}")

        self.rate = rate
        self.capacity = capacity
        self._clock = clock
        self._sleep = sleep
        self._tokens = 0.0
        self._updated = clock()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> float:
        """Block until `tokens` are available. Returns seconds spent waiting."""
        if tokens > self.capacity:
            raise ValueError(f"cannot acquire {tokens} tokens from a bucket of {self.capacity}")

        waited = 0.0
        with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return waited
                delay = (tokens - self._tokens) / self.rate
                self._sleep(delay)
                waited += delay

    def _refill(self) -> None:
        now = self._clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._updated) * self.rate)
        self._updated = now


# The single limiter every EDGAR call shares. Module-level so that no code path
# can accidentally construct its own and double the effective request rate.
_EDGAR_LIMITER = RateLimiter(EDGAR_RATE_LIMIT)


def edgar_limiter() -> RateLimiter:
    return _EDGAR_LIMITER
