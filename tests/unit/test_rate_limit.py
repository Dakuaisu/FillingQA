"""Tests for the EDGAR token-bucket limiter.

Most of these run on an injected fake clock so the pacing arithmetic is checked
exactly and instantly. One test spends real wall-clock time, because a limiter
that only works against a fake clock protects nothing.
"""

from __future__ import annotations

import itertools
import time

import pytest

from api.ingest.rate_limit import EDGAR_RATE_LIMIT, RateLimiter, edgar_limiter


class FakeClock:
    """A clock that only advances when someone sleeps."""

    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def make_limiter(rate: float = EDGAR_RATE_LIMIT, capacity: float = 1.0):
    clock = FakeClock()
    limiter = RateLimiter(rate, capacity=capacity, clock=clock.time, sleep=clock.sleep)
    return limiter, clock


def test_paces_twenty_requests_over_at_least_two_and_a_half_seconds():
    # 20 requests at 8/s with no burst allowance: every one pays a full
    # 125ms interval, including the first, because the bucket starts empty.
    limiter, clock = make_limiter()
    for _ in range(20):
        limiter.acquire()
    assert clock.now == pytest.approx(2.5)


def test_first_acquire_is_not_free():
    limiter, clock = make_limiter()
    waited = limiter.acquire()
    assert waited == pytest.approx(0.125)
    assert clock.now == pytest.approx(0.125)


def test_interval_between_consecutive_acquires_is_never_below_the_rate():
    limiter, clock = make_limiter()
    stamps = []
    for _ in range(10):
        limiter.acquire()
        stamps.append(clock.now)
    gaps = [b - a for a, b in itertools.pairwise(stamps)]
    interval = 1 / EDGAR_RATE_LIMIT
    assert min(gaps) >= interval - 1e-9, f"gaps {gaps} dip below {interval}s"


def test_no_more_than_rate_requests_in_any_one_second_window():
    limiter, clock = make_limiter()
    stamps = []
    for _ in range(40):
        limiter.acquire()
        stamps.append(clock.now)
    for start in stamps:
        in_window = [t for t in stamps if start <= t < start + 1.0]
        assert len(in_window) <= EDGAR_RATE_LIMIT


def test_capacity_allows_a_burst_only_after_idling_to_earn_it():
    limiter, clock = make_limiter(capacity=8.0)
    clock.now += 1.0  # idle long enough to refill the whole bucket
    before = clock.now
    for _ in range(8):
        limiter.acquire()
    assert clock.now == before  # the burst is free
    limiter.acquire()  # the ninth is not
    assert clock.now == pytest.approx(before + 0.125)


def test_acquiring_more_than_capacity_is_rejected():
    limiter, _ = make_limiter(capacity=1.0)
    with pytest.raises(ValueError, match="cannot acquire"):
        limiter.acquire(2.0)


@pytest.mark.parametrize(("rate", "capacity"), [(0, 1), (-1, 1), (8, 0), (8, 0.5)])
def test_invalid_construction_is_rejected(rate, capacity):
    with pytest.raises(ValueError):
        RateLimiter(rate, capacity=capacity)


def test_edgar_limiter_is_a_shared_singleton():
    # Two callers constructing their own limiters would double the real request
    # rate, which is the failure mode this module exists to prevent.
    assert edgar_limiter() is edgar_limiter()
    assert edgar_limiter().rate == EDGAR_RATE_LIMIT


def test_real_wall_clock_pacing_of_twenty_requests():
    """The assertion from the build plan, against the real clock."""
    limiter = RateLimiter(EDGAR_RATE_LIMIT)
    start = time.monotonic()
    for _ in range(20):
        limiter.acquire()
    elapsed = time.monotonic() - start
    assert elapsed > 2.4, f"20 requests took {elapsed:.3f}s, expected > 2.4s"
