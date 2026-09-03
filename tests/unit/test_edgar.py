"""Tests for the EDGAR client: User-Agent enforcement, retry policy, caching.

No network. Retry behavior is driven through httpx's MockTransport so the policy
is tested exactly, and the fake sleep records delays instead of spending them.
"""

from __future__ import annotations

import json

import httpx
import pytest

from api import config
from api.config import ConfigError, sec_user_agent
from api.ingest.edgar import (
    BACKOFF_CAP_S,
    EdgarClient,
    EdgarError,
    backoff_delay,
)
from api.ingest.rate_limit import RateLimiter


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch, tmp_path):
    """Never let a developer's real .env decide what these tests see."""
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "absent.env")
    monkeypatch.setattr(config, "_loaded", False)
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.setenv("SEC_USER_AGENT", "FilingQA Test suite dev@filingqa.test")


class FakeSleep:
    def __init__(self) -> None:
        self.delays: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


class FakeClock:
    """A clock that only advances when someone sleeps on it.

    The limiter refills from elapsed time, so a clock that never advances would
    starve it and spin forever. It has to move when slept on.
    """

    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def make_client(handler, tmp_path, **kwargs) -> tuple[EdgarClient, FakeSleep]:
    sleep = FakeSleep()
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    # The limiter runs on its own fake clock so pacing costs no real time here.
    clock = FakeClock()
    limiter = RateLimiter(8.0, clock=clock.time, sleep=clock.sleep)
    client = EdgarClient(
        cache_dir=tmp_path / "cache",
        limiter=limiter,
        client=http,
        sleep=sleep,
        **kwargs,
    )
    return client, sleep


# ------------------------------------------------------------- user agent


@pytest.mark.parametrize(
    "value",
    ["", "   ", "FilingQA Research Project", "no-email-here"],
)
def test_missing_or_emailless_user_agent_is_a_hard_stop(monkeypatch, value):
    monkeypatch.setenv("SEC_USER_AGENT", value)
    with pytest.raises(ConfigError):
        sec_user_agent()


def test_placeholder_address_is_rejected(monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "FilingQA Project your.name@example.com")
    with pytest.raises(ConfigError, match="placeholder"):
        sec_user_agent()


def test_valid_user_agent_is_returned_verbatim(monkeypatch):
    monkeypatch.setenv("SEC_USER_AGENT", "FilingQA Research a.person@somewhere.org")
    assert sec_user_agent() == "FilingQA Research a.person@somewhere.org"


def test_client_construction_fails_before_any_request(monkeypatch, tmp_path):
    monkeypatch.setenv("SEC_USER_AGENT", "")
    with pytest.raises(ConfigError):
        EdgarClient(cache_dir=tmp_path / "cache")


def test_user_agent_header_is_sent(tmp_path):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["ua"] = request.headers.get("User-Agent")
        return httpx.Response(200, content=b"ok")

    client, _ = make_client(handler, tmp_path)
    client.fetch_bytes("https://example.invalid/x", tmp_path / "x.bin")
    assert "dev@filingqa.test" in seen["ua"]


# ----------------------------------------------------------------- backoff


def test_backoff_is_exponential_and_capped():
    assert [backoff_delay(i) for i in range(5)] == [1.0, 2.0, 4.0, 8.0, 16.0]
    assert backoff_delay(20) == BACKOFF_CAP_S


def test_retry_after_header_overrides_exponential():
    assert backoff_delay(0, retry_after="7") == 7.0
    assert backoff_delay(3, retry_after="2") == 2.0


def test_retry_after_is_capped_and_survives_http_date():
    assert backoff_delay(0, retry_after="9999") == BACKOFF_CAP_S
    # An HTTP-date Retry-After is not parsed; fall back to exponential.
    assert backoff_delay(2, retry_after="Wed, 21 Oct 2026 07:28:00 GMT") == 4.0


# ------------------------------------------------------------------- retry


def test_429_is_retried_then_succeeds(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, content=b"finally")

    client, sleep = make_client(handler, tmp_path)
    body = client.fetch_bytes("https://example.invalid/x", tmp_path / "x.bin")
    assert body == b"finally"
    assert calls["n"] == 3
    assert sleep.delays == [2.0, 2.0]


def test_503_is_retried_until_attempts_run_out(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client, sleep = make_client(handler, tmp_path, max_attempts=4)
    with pytest.raises(EdgarError, match="after 4 attempts"):
        client.fetch_bytes("https://example.invalid/x", tmp_path / "x.bin")
    assert sleep.delays == [1.0, 2.0, 4.0]  # no sleep after the final attempt


def test_403_is_not_retried_and_names_the_user_agent(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(403)

    client, sleep = make_client(handler, tmp_path)
    with pytest.raises(EdgarError, match="User-Agent"):
        client.fetch_bytes("https://example.invalid/x", tmp_path / "x.bin")
    assert calls["n"] == 1
    assert sleep.delays == []


def test_404_is_not_retried(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404)

    client, _ = make_client(handler, tmp_path)
    with pytest.raises(EdgarError, match="HTTP 404"):
        client.fetch_bytes("https://example.invalid/x", tmp_path / "x.bin")
    assert calls["n"] == 1


def test_connection_errors_are_retried(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, content=b"ok")

    client, sleep = make_client(handler, tmp_path)
    assert client.fetch_bytes("https://example.invalid/x", tmp_path / "x.bin") == b"ok"
    assert sleep.delays == [1.0]


# ------------------------------------------------------------------- cache


def test_second_fetch_is_served_from_disk_without_a_request(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, content=b"payload")

    client, _ = make_client(handler, tmp_path)
    dest = tmp_path / "raw" / "doc.htm"

    assert client.fetch_bytes("https://example.invalid/d", dest) == b"payload"
    assert client.fetch_bytes("https://example.invalid/d", dest) == b"payload"
    assert calls["n"] == 1, "cached response should not re-contact SEC"
    assert dest.read_bytes() == b"payload"


def test_refresh_forces_a_re_fetch(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, content=f"body{calls['n']}".encode())

    client, _ = make_client(handler, tmp_path)
    dest = tmp_path / "doc.htm"
    client.fetch_bytes("https://example.invalid/d", dest)
    assert client.fetch_bytes("https://example.invalid/d", dest, refresh=True) == b"body2"
    assert calls["n"] == 2


def test_no_partial_file_survives_a_failed_download(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client, _ = make_client(handler, tmp_path, max_attempts=1)
    dest = tmp_path / "raw" / "doc.htm"
    with pytest.raises(EdgarError):
        client.fetch_bytes("https://example.invalid/d", dest)
    assert not dest.exists()
    assert not list(tmp_path.glob("**/*.part"))


# --------------------------------------------------------------- endpoints


def test_resolve_cik_zero_pads_to_ten_characters(tmp_path):
    payload = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 909832, "ticker": "COST", "title": "COSTCO WHOLESALE CORP"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=json.dumps(payload).encode())

    client, _ = make_client(handler, tmp_path)
    assert client.resolve_cik("AAPL") == "0000320193"
    assert client.resolve_cik("cost") == "0000909832"
    assert len(client.resolve_cik("AAPL")) == 10


def test_unknown_ticker_is_named_in_the_error(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"{}")

    client, _ = make_client(handler, tmp_path)
    with pytest.raises(EdgarError, match="NOTATICKER"):
        client.resolve_cik("NOTATICKER")
