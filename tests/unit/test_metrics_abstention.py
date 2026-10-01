"""Abstention 2x2 (PRD 11.2). Synthetic verdicts."""

from __future__ import annotations

import pytest

from eval.metrics.abstention import TwoByTwo, rates, two_by_two


def test_cells_and_rates():
    rows = ([(False, "PASS")] * 8 + [(False, "ABSTAIN")] * 2
            + [(True, "PASS")] * 1 + [(True, "ABSTAIN")] * 4)  # fmt: skip
    t = two_by_two(rows)
    assert t == TwoByTwo(answered_answerable=8, abstained_answerable=2,
                         answered_unanswerable=1, abstained_unanswerable=4)  # fmt: skip
    r = rates(t)
    assert r["false_answer_rate"] == pytest.approx(1 / 5)
    assert r["over_abstention_rate"] == pytest.approx(2 / 10)
    assert r["abstention_precision"] == pytest.approx(4 / 6)
    assert r["abstention_recall"] == pytest.approx(4 / 5)
    assert r["abstention_f1"] == pytest.approx(2 * (4 / 6) * (4 / 5) / (4 / 6 + 4 / 5))


def test_partial_has_no_cell_yet_and_unknown_verdicts_fail():
    with pytest.raises(NotImplementedError, match="F-21"):
        two_by_two([(False, "PARTIAL")])
    with pytest.raises(ValueError):
        two_by_two([(False, "MAYBE")])


def test_empty_rows_give_no_rates():
    assert set(rates(two_by_two([])).values()) == {None}
