"""The gold rule (F-32, F-72) on real span rows.

tests/fixtures/xbrl_gold_spans.json is written by
`python -m scripts.xbrl_pool --write-fixture`: every span of two real keys.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from eval.generate.gold import Span, select_gold

DOC = json.loads(
    (Path(__file__).resolve().parent.parent / "fixtures" / "xbrl_gold_spans.json").read_text(
        encoding="utf-8"
    )
)
KEYS = {(k["accession"], k["concept"]): k for k in DOC["keys"]}


def selection(accession, concept):
    k = KEYS[(accession, concept)]
    spans = [
        Span(s["chunk_id"], Decimal(s["value"]), s["raw_text"], s["scale"], s["dimensional"])
        for s in k["spans"]
    ]
    return select_gold(Decimal(k["fact_value"]), spans)


def test_rounded_mention_is_not_gold():
    # PFE total assets 201,131 million; chunk 410.0:414.0 prints "201" (billion), F-72.
    sel = selection("0000078003-26-000095", "us-gaap:Assets")
    assert sel.gold == ("0000078003-26-000095:65.0:65.0",)
    assert sel.prd_key_count == 2  # PRD 6.5.3's literal key would count the rounded one
    assert [s.raw_text for s in sel.exact] == ["201,131"]


def test_dimensional_span_is_not_gold_even_at_the_same_value():
    # AAPL FY2024 net income 93,736 million; chunk 408.0 holds it on a dimensional
    # (equity-statement column) context, F-32.
    sel = selection("0000320193-25-000079", "us-gaap:NetIncomeLoss")
    assert "0000320193-25-000079:408.0:408.0" not in sel.gold
    assert sel.gold == tuple(
        f"0000320193-25-000079:{c}:{c}" for c in ("390.0", "396.0", "414.0", "462.0")
    )
    assert sel.prd_key_count == 4 and sel.has_span


def test_no_company_level_span_means_no_gold():
    k = KEYS[("0000320193-25-000079", "us-gaap:NetIncomeLoss")]
    dim = [
        Span(s["chunk_id"], Decimal(s["value"]), s["raw_text"], s["scale"], s["dimensional"])
        for s in k["spans"]
        if s["dimensional"]
    ]
    sel = select_gold(Decimal(k["fact_value"]), dim)
    assert sel.gold == () and not sel.has_span and sel.prd_key_count == 0


def test_fixture_is_stamped_with_the_freeze_versions():
    import yaml

    from scripts.write_freeze import FREEZE_FILE

    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    assert DOC["parser_version"] == record["parser_version"]
    assert DOC["chunker_version"] == record["chunker_version"]
