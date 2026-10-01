"""Numeric accuracy (F-81 decided). Inline answers; reference shapes from the candidates."""

from __future__ import annotations

from decimal import Decimal

import pytest

from eval.metrics.numeric import aggregate, mask, score_item, text_figures


def xbrl(ref):
    return {"item_id": "x", "question_type": "xbrl_numeric", "reference_answer": ref, "tags": []}


def seeded(ref, scale_tag):
    return {"item_id": "s", "question_type": "table", "reference_answer": ref,
            "tags": ["AAPL", "kind:factual", scale_tag]}  # fmt: skip


COMP = {"item_id": "c", "question_type": "comparison", "tags": [], "reference_answer":
        "-$216 million for the third quarter of fiscal 2025, compared with -$964 million for "
        "the third quarter of fiscal 2023: an increase of $748 million."}  # fmt: skip
INV = xbrl("$7,286 million as of September 28, 2024.")


def ans(text, claims=None, abstained=False):
    return {"text": text, "claims": claims or [], "abstained": abstained}


@pytest.mark.parametrize(
    "text",
    ["Q2", "FY2026", "fiscal 2025", "fiscal year 2024", "10-Q", "Form 10-K", "March 28, 2026",
     "Sep 28, 2024", "28, 2026", "2024-09-28", "Item 7", "Item 1A", "Note 18", "24 weeks",
     "six months", "in 2024", "Part II"],
)  # fmt: skip
def test_labels_dates_forms_items_and_years_are_not_figures(text):
    assert text_figures(text) == [], mask(text)


def test_figures_with_scale_words_and_signs():
    figs = text_figures("Q2 FY2026: $7.286 billion, (28), -$691 million, 44.1%, $6.08 per share")
    assert [f.value for f in figs] == [
        Decimal("7.286") * 10**9,
        Decimal(-28),
        Decimal(-691) * 10**6,
        Decimal("44.1"),
        Decimal("6.08"),
    ]
    assert [f.explicit_sign for f in figs] == [False, True, True, False, False]


def test_exact_at_the_references_printed_precision():
    assert score_item(INV, ans("Inventories were $7,286 million.")).correct
    assert score_item(INV, ans("About $7.286 billion.")).correct
    assert score_item(INV, ans("$7,286.4 million")).correct  # rounds to the reference's digit
    s = score_item(INV, ans("About $7.3 billion."))  # 0.19% off: not exact, within 0.5%
    assert not s.correct and s.tolerant
    s = score_item(INV, ans("About $7.4 billion."))  # 1.6% off
    assert not s.correct and not s.tolerant


def test_dates_in_the_answer_never_match():
    # F-97's case: "Unknown" plus a period label must not score against a small figure.
    eps = xbrl("$2.01 for the three months ended March 28, 2026.")
    s = score_item(eps, ans("Unknown; see its Q2 FY2026 10-Q filed after March 28, 2026."))
    assert not s.correct and s.figure_count == 0


def test_magnitude_only_with_sign_agreement_reported():
    tax = xbrl("-$28 million for the fiscal year ended December 31, 2024.")
    for text in ("A benefit of $28 million.", "(28) million", "-$28 million"):
        assert score_item(tax, ans(text)).correct, text
    assert score_item(tax, ans("A benefit of $28 million.")).sign_agree is None  # no sign stated
    assert score_item(tax, ans("-$28 million")).sign_agree is True
    assert score_item(tax, ans("$28 million")).sign_agree is None
    pos = xbrl("$2,815 million for the six months ended February 15, 2026.")
    assert score_item(pos, ans("(2,815) million")).sign_agree is False


def test_claim_figure_objects_come_first_and_fallback_is_counted():
    claims = [{"claim_id": "c1", "text": "...", "figure": {"value": 7286, "unit": "millions"}}]
    s = score_item(INV, ans("Text says 9,999 million.", claims))
    assert s.correct and not s.fallback
    s = score_item(INV, ans("$7,286 million"))
    assert s.correct and s.fallback


def test_any_figure_is_gated_strict_first_figure_reported():
    s = score_item(INV, ans("$6,331 million a year earlier; $7,286 million now."))
    assert s.correct and not s.strict and s.figure_count == 2


def test_zero_words_only_for_a_zero_reference_and_an_answered_item():
    zero = xbrl("$0 million for the fiscal year ended December 31, 2024.")
    assert score_item(zero, ans("None.")).correct
    assert score_item(zero, ans("-")).correct
    assert not score_item(zero, ans("None.", abstained=True)).correct
    assert not score_item(INV, ans("None.")).correct


def test_comparison_needs_both_values_and_the_difference():
    full = ans("-$216 million vs -$964 million, an increase of $748 million.")
    s = score_item(COMP, full)
    assert s.correct and s.values_only
    s = score_item(COMP, ans("It went from $964 million to $216 million."))
    assert not s.correct and s.values_only
    assert not score_item(COMP, ans("An increase of $748 million.")).correct


def test_seeded_scale_from_tags_and_unknown_is_excluded():
    s = score_item(seeded("$98,016", "unit_scale_millions"), ans("$98.016 billion"))
    assert s.correct
    s = score_item(seeded("(1,434)", "unit_scale_millions"), ans("$1,434 million"))
    assert s.correct
    s = score_item(seeded("44.1%", "unit_scale_unknown"), ans("44.1%"))
    assert s.excluded == "unit_scale_unknown"
    synth = {"item_id": "y", "question_type": "synthesis", "reference_answer": "x",
             "tags": ["kind:interpretive"]}  # fmt: skip
    assert score_item(synth, ans("x")).excluded == "not numeric"


def test_aggregate_prints_exclusions_and_variants():
    scores = [
        score_item(INV, ans("$7,286 million")),
        score_item(INV, ans("$7.3 billion")),
        score_item(INV, ans("", abstained=True)),
        score_item(seeded("44.1%", "unit_scale_unknown"), ans("44.1%")),
    ]
    a = aggregate(scores)
    assert a["n"] == 3 and a["excluded"] == {"unit_scale_unknown": 1}
    assert a["numeric_accuracy"] == pytest.approx(1 / 3)
    assert a["tolerant_0_5pct"] == pytest.approx(2 / 3)
    assert a["abstained"] == 1  # stays in the denominator as incorrect (F-81)
    assert a["figure_count_distribution"] == {"0": 1, "1": 2}
