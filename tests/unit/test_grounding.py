"""Numeric grounding (PRD 7.5): the forms PRD 7.5 lists, and F-82, F-85, F-87. Inline data."""

from __future__ import annotations

from decimal import Decimal

from api.verify.grounding import (
    chunk_numbers,
    claim_numbers,
    ground_answer,
    period_stated,
)

TABLE = """[Apple Inc. (AAPL) | 10-K | FY2024 | Part II, Item 8]
[Table: Consolidated Balance Sheets | Apple Inc. | FY2024 10-K | Part II, Item 8 | in millions, USD]
| | September 28, 2024 | September 30, 2023 |
|---|---|---|
| Inventories | 7,286 | 6,331 |
| Payments for repurchase of common stock | (94,949) | (77,550) |"""
EPS = """[Table: Net Income Per Share | NVIDIA | Q2 FY2027 10-Q | in millions, USD]
(In millions, except per share data)
| Diluted net income per share | $ 1.08 | $ 0.67 |"""
PROSE = "Revenue was $391.0 billion in fiscal 2024, up 2% from the prior year."
NIL = """[Table: Share repurchases | Pfizer | FY2024 10-K | in millions, USD]
| Purchases of common stock | — | 2,000 |"""
FIG = {"value": 7286, "unit": "millions", "currency": "USD", "period": "FY2024",
       "concept": "Inventories"}  # fmt: skip


def claim(text, cites=("t",), fig=None, cid="c1"):
    return {"claim_id": cid, "text": text, "citations": list(cites), "figure": fig}


def one(text, fig=None, chunks=None, zero=frozenset()):
    chunks = chunks or {"t": TABLE}
    return ground_answer([claim(text, tuple(chunks), fig)], chunks, set(zero))[0]


def test_every_printed_form_in_prd_7_5_grounds_against_a_scaled_table():
    for text in ("Inventories were $7,286 million as of September 28, 2024.",
                 "Inventories were 7,286 million in fiscal 2024.",
                 "Inventories were 7286 million in FY2024.",
                 "Inventories were $7.286 billion in fiscal 2024."):  # fmt: skip
        r = one(text, FIG)
        assert r["numbers_grounded"] and r["unit_ok"], text
    # The year in the date and the fiscal year are masked, never "numbers".
    assert [
        n["printed"] for n in one("Inventories were $7,286 million in fiscal 2024.")["numbers"]
    ] == ["$7,286 million"]


def test_f87_sign_is_not_part_of_grounding():
    fig = {**FIG, "value": 94949, "concept": "Share repurchases"}
    assert one("Apple paid $94,949 million for share repurchases in fiscal 2024.", fig)[
        "numbers_grounded"
    ]
    assert one("Share repurchases were $(94,949) million in fiscal 2024.", fig)["numbers_grounded"]


def test_a_number_printed_nowhere_or_at_another_scale_is_not_grounded():
    assert not one("Inventories were $7,300 million in fiscal 2024.", {**FIG, "value": 7300})[
        "numbers_grounded"
    ]
    assert not one("Inventories were $7.3 billion in fiscal 2024.")["numbers_grounded"]
    bad = one("Inventories were $7,286 thousand in fiscal 2024.", {**FIG, "unit": "thousands"})
    assert not bad["numbers_grounded"] and bad["unit_ok"] is False


def test_unit_scale_catches_a_figure_object_with_the_wrong_scale():
    r = one("Inventories were 7,286 in fiscal 2024.", {**FIG, "unit": "ones"})
    assert r["numbers_grounded"] and r["unit_ok"] is False  # printed as is in a millions table
    assert one("Inventories were 7,286 in fiscal 2024.")["unit_ok"] is None  # no figure object


def test_per_share_figures_in_a_millions_table_that_says_except_per_share():
    fig = {"value": 1.08, "unit": "ones", "currency": "USD", "period": "Q2 FY2027",
           "concept": "EPS diluted"}  # fmt: skip
    r = one("Diluted EPS was $1.08 for Q2 FY2027.", fig, {"e": EPS})
    assert r["numbers_grounded"] and r["unit_ok"]


def test_prose_scale_words_and_percentages():
    fig = {"value": 391.0, "unit": "billions", "currency": "USD", "period": "FY2024",
           "concept": "Revenue"}  # fmt: skip
    r = one("Revenue was $391.0 billion in fiscal 2024.", fig, {"p": PROSE})
    assert r["numbers_grounded"] and r["unit_ok"]
    assert one("Revenue grew 2% in fiscal 2024.", None, {"p": PROSE})["numbers_grounded"]
    assert not one("Revenue grew 3% in fiscal 2024.", None, {"p": PROSE})["numbers_grounded"]


def test_f82_zero_is_grounded_by_a_nil_span_not_by_any_dash():
    fig = {"value": 0, "unit": "millions", "currency": "USD", "period": "FY2024",
           "concept": "Share repurchases"}  # fmt: skip
    text = "Pfizer's share repurchases were $0 million in fiscal 2024."
    assert one(text, fig, {"n": NIL}, zero={"n"})["numbers_grounded"]
    assert not one(text, fig, {"n": NIL})["numbers_grounded"]


def test_f85_differences_and_percent_changes_of_the_answers_own_figures():
    chunks = {"t": TABLE}
    c1 = claim("Inventories were $7,286 million in fiscal 2024.", fig=FIG, cid="c1")
    c2 = claim("Inventories were $6,331 million in fiscal 2023.", fig={**FIG, "value": 6331},
               cid="c2")  # fmt: skip
    diff = claim("Inventories rose $955 million from fiscal 2023 to fiscal 2024.",
                 fig={**FIG, "value": 955}, cid="c3")  # fmt: skip
    pct = claim("That is an increase of 15.1% over fiscal 2023.", cid="c4")
    wrong = claim("Inventories rose $956 million in fiscal 2024.", fig={**FIG, "value": 956},
                  cid="c5")  # fmt: skip
    r = ground_answer([c1, c2, diff, pct, wrong], chunks, set())
    assert [x["numbers_grounded"] for x in r] == [True, True, True, True, False]
    assert [x["numbers_derived"] for x in r] == [False, False, True, True, False]
    # A derived figure's scale follows its operands (smoke run 4d1f5ce1e3f2, cmp_0010).
    assert [x["unit_ok"] for x in r] == [True, True, True, None, False]
    # A difference alone, without the answer's own grounded figures, is not derived.
    assert not ground_answer([diff], chunks, set())[0]["numbers_grounded"]


def test_only_the_claims_own_cited_chunks_count():
    r = ground_answer([claim("Inventories were $7,286 million in fiscal 2024.", ("p",), FIG)],
                      {"t": TABLE, "p": PROSE}, set())  # fmt: skip
    assert not r[0]["numbers_grounded"] and r[0]["citations_supporting"] == []


def test_period_stated_and_number_reading():
    assert period_stated("Inventories were $7,286 million as of September 28, 2024.")
    assert period_stated("Net income for Q3 FY2024 was $21,448 million.")
    assert not period_stated("Inventories were $7,286 million.")
    n = claim_numbers("Up 15% to $7.286 billion.", None)
    assert [(x.value, x.pct) for x in n] == [(Decimal(15), True), (Decimal("7286000000"), False)]
    assert chunk_numbers(TABLE).scaled == {Decimal(v) * 10**6 for v in (7286, 6331, 94949, 77550)}
