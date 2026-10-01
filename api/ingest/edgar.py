"""HTTP client for SEC EDGAR.

Every request goes through the shared rate limiter (PRD 6.1, 8 req/s) and every
response is written to disk before anyone parses it. The disk cache is not a
performance optimization -- it exists so that re-running ingestion during
development never re-contacts SEC. PRD 16 rates an IP block as the highest-cost
failure available to this project, and the way you get one is by re-downloading
the same 10-K forty times while iterating on a parser.

Retry policy is hand-rolled and lives in `_request` so it stays visible and
defensible, rather than behind a decorator from another library.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

from api.config import data_dir, sec_user_agent
from api.ingest.rate_limit import RateLimiter, edgar_limiter

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# Retried with exponential backoff. 429 is SEC telling us to slow down; the 5xx
# family is transient server-side failure. Anything else -- notably 403, which is
# what a User-Agent problem looks like, and 404 -- is a bug on our side and is
# raised immediately rather than hammered at.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})

MAX_ATTEMPTS = 5
BACKOFF_BASE_S = 1.0
BACKOFF_CAP_S = 60.0
REQUEST_TIMEOUT_S = 30.0


class EdgarError(RuntimeError):
    """A request to EDGAR failed in a way we should not retry past."""


def backoff_delay(attempt: int, retry_after: str | None = None) -> float:
    """Seconds to wait before retry number `attempt` (0-based).

    Exponential: 1s, 2s, 4s, 8s ... capped. A Retry-After header, when SEC sends
    one, always wins -- it is the server telling us exactly how long it wants,
    and guessing shorter is how a soft throttle becomes a block.
    """
    if retry_after:
        try:
            return min(float(retry_after), BACKOFF_CAP_S)
        except ValueError:
            pass  # Retry-After may be an HTTP-date; fall through to exponential
    return min(BACKOFF_BASE_S * (2**attempt), BACKOFF_CAP_S)


class EdgarClient:
    """Rate-limited, retrying, disk-cached HTTP client for EDGAR.

    Usable as a context manager. `cache_dir` defaults to `<DATA_DIR>/cache`.
    """

    def __init__(
        self,
        *,
        cache_dir: Path | None = None,
        limiter: RateLimiter | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> None:
        # Resolved eagerly: a bad User-Agent should fail at construction, before
        # any caller has a client object it believes is usable.
        self.user_agent = sec_user_agent()

        self.cache_dir = cache_dir if cache_dir is not None else data_dir() / "cache"
        self._limiter = limiter if limiter is not None else edgar_limiter()
        self._sleep = sleep
        self._max_attempts = max_attempts

        # Sent explicitly on every request rather than left to client defaults.
        # An injected client would otherwise carry httpx's own User-Agent, and a
        # missing contact header is the one mistake SEC blocks for (PRD 6.1).
        self._headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        }

        self._owns_client = client is None
        self._client = (
            client
            if client is not None
            else httpx.Client(timeout=REQUEST_TIMEOUT_S, follow_redirects=True)
        )

    # ------------------------------------------------------------- lifecycle

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> EdgarClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --------------------------------------------------------------- request

    def _request(self, url: str) -> httpx.Response:
        """GET `url`, paced and retried. Raises EdgarError once attempts run out."""
        last: str = "no attempt made"

        for attempt in range(self._max_attempts):
            self._limiter.acquire()
            try:
                response = self._client.get(url, headers=self._headers)
            except httpx.RequestError as exc:
                # Connection-level failure: no response to inspect, so treat it
                # as transient and back off the same way.
                last = f"{type(exc).__name__}: {exc}"
                if attempt + 1 >= self._max_attempts:
                    break
                self._sleep(backoff_delay(attempt))
                continue

            if response.status_code == 200:
                return response

            if response.status_code in RETRY_STATUSES:
                last = f"HTTP {response.status_code}"
                if attempt + 1 >= self._max_attempts:
                    break
                self._sleep(backoff_delay(attempt, response.headers.get("Retry-After")))
                continue

            # Not retryable. 403 usually means the User-Agent was rejected.
            hint = ""
            if response.status_code == 403:
                hint = (
                    " -- SEC rejects requests without a descriptive User-Agent "
                    "containing real contact information (PRD 6.1)"
                )
            raise EdgarError(f"GET {url} failed with HTTP {response.status_code}{hint}")

        raise EdgarError(f"GET {url} failed after {self._max_attempts} attempts ({last})")

    # ----------------------------------------------------------------- cache

    def fetch_bytes(self, url: str, cache_path: Path, *, refresh: bool = False) -> bytes:
        """Return the body at `url`, reading from `cache_path` when it exists.

        The cache is checked before the rate limiter, so a fully cached run makes
        no network calls at all and takes no pacing delay.
        """
        if cache_path.exists() and not refresh:
            return cache_path.read_bytes()

        body = self._request(url).content

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temporary neighbour and rename, so an interrupted run cannot
        # leave a truncated file that later looks like a valid cache hit.
        tmp = cache_path.with_suffix(cache_path.suffix + ".part")
        tmp.write_bytes(body)
        tmp.replace(cache_path)
        return body

    def fetch_json(
        self, url: str, cache_path: Path, *, refresh: bool = False, exact: bool = False
    ) -> Any:
        """`exact` parses non-integer numbers as Decimal: companyfacts values feed
        NUMERIC columns, and a float does not hold 7.46 exactly."""
        body = self.fetch_bytes(url, cache_path, refresh=refresh)
        return json.loads(body, parse_float=Decimal) if exact else json.loads(body)

    # ------------------------------------------------------------- endpoints

    def company_tickers(self, *, refresh: bool = False) -> dict[str, str]:
        """Map uppercase ticker -> zero-padded 10-character CIK."""
        raw = self.fetch_json(
            COMPANY_TICKERS_URL,
            self.cache_dir / "company_tickers.json",
            refresh=refresh,
        )
        # Shape is {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "..."}, ...}
        return {entry["ticker"].upper(): f"{int(entry['cik_str']):010d}" for entry in raw.values()}

    def resolve_cik(self, ticker: str, *, refresh: bool = False) -> str:
        ticker = ticker.upper()
        mapping = self.company_tickers(refresh=refresh)
        try:
            return mapping[ticker]
        except KeyError:
            raise EdgarError(f"ticker {ticker!r} is not in SEC's company_tickers.json") from None

    def fetch_submissions(self, cik: str, *, refresh: bool = False) -> dict[str, Any]:
        cik = f"{int(cik):010d}"
        return self.fetch_json(
            SUBMISSIONS_URL.format(cik=cik),
            self.cache_dir / "submissions" / f"CIK{cik}.json",
            refresh=refresh,
        )

    def fetch_companyfacts(self, cik: str, *, refresh: bool = False) -> dict[str, Any]:
        cik = f"{int(cik):010d}"
        return self.fetch_json(
            COMPANYFACTS_URL.format(cik=cik),
            self.cache_dir / "companyfacts" / f"CIK{cik}.json",
            refresh=refresh,
            exact=True,
        )

    def download_document(self, url: str, dest: Path, *, refresh: bool = False) -> bytes:
        """Fetch a filing document, caching it at `dest` (typically under data/raw/)."""
        return self.fetch_bytes(url, dest, refresh=refresh)
