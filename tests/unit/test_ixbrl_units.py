"""xbrli:unit resolution, on the unit declarations of a real filing."""

from __future__ import annotations

from api.parse.ixbrl import extract
from tests.conftest import AAPL_10K, fixture_bytes


def test_monetary_means_a_bare_currency_measure():
    units = extract(fixture_bytes(AAPL_10K)).units
    assert units["usd"].is_monetary
    # A divide with USD on top is a per-share amount -- the "except" set.
    assert not units["usdPerShare"].is_monetary
    assert not units["shares"].is_monetary
    assert not units["number"].is_monetary  # xbrli:pure
