"""The no-context match rule (TRADEOFFS: no-context filter rule). Answers inline."""

from __future__ import annotations

from decimal import Decimal

from api.config import REPO_ROOT
from eval.generate.no_context import figures, match, render

M = Decimal(10) ** 6


def test_scale_words_normalize_each_figure():
    got = {f.text: f.value for f in figures("About $1.4 billion, or 1,434 million; 250 thousand.")}
    assert got["$1.4 billion"] == Decimal("1.4") * 10**9
    assert got["1,434 million"] == 1434 * M
    assert got["250 thousand"] == 250_000


def test_exact_and_within_half_a_percent_drop():
    assert match("It was $1,434 million.", Decimal("-1434"), 1434 * M).dropped
    # 1,440 vs 1,434 is 0.42% off: the PRD's tolerance accepts it as the same figure.
    assert match("Roughly $1.44 billion.", Decimal("1434"), 1434 * M).dropped


def test_rounded_answer_is_a_near_match_not_a_drop():
    m = match("About $1.4 billion.", Decimal("1434"), 1434 * M)  # 2.4% off
    assert not m.dropped and m.near
    far = match("About $2 billion.", Decimal("1434"), 1434 * M)
    assert not far.dropped and not far.near


def test_bare_number_is_not_scaled_into_a_match():
    # "1,434" with no scale word is 1,434, not 1,434 million.
    assert not match("It was 1,434.", Decimal("1434"), 1434 * M).dropped


def test_percent_and_per_share_compare_as_plain_values():
    assert match("Gross margin was 44.1%.", Decimal("44.1"), Decimal("44.1")).dropped
    assert not match("Gross margin was 46%.", Decimal("44.1"), Decimal("44.1")).dropped
    assert match("Diluted EPS was $6.13.", Decimal("6.13"), Decimal("6.13")).dropped


def test_digits_only_path_when_scale_is_unknown_or_mixed():
    m = match("JPMorgan reported $4.44 per share.", Decimal("4.44"), None)
    assert m.dropped and m.digits_only
    assert not match("It was $4.10.", Decimal("4.44"), None).dropped


def test_sign_only_disagreement_is_counted_but_still_drops():
    m = match("Net cash used was -$1,434 million.", Decimal("1434"), 1434 * M)
    assert m.dropped and m.sign_only
    same = match("Net cash used was (1,434) million.", Decimal("-1434"), -1434 * M)
    assert same.dropped and not same.sign_only


def test_unknown_or_no_figure_is_not_a_match():
    m = match("Unknown.", Decimal("1434"), 1434 * M)
    assert not m.dropped and m.unknown
    assert not match("I cannot say.", Decimal("1434"), 1434 * M).dropped


def test_prompt_file_holds_the_question_and_the_instruction():
    template = (REPO_ROOT / "eval/generate/prompts/no_context_v1.txt").read_text(encoding="utf-8")
    out = render(template, "What was X?")
    assert out.startswith("What was X?\n")
    assert "Answer from your own knowledge; if you do not know, say unknown." in out
