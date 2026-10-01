"""The abstention 2x2 (PRD 11.2). Pure.

Rows: should the system abstain (`expected_abstain`); columns: did it (verdict
ABSTAIN) or did it answer (PASS or PARTIAL). PARTIAL counts as answered (F-21):
on an unanswerable item it is a failure to abstain, on an answerable one the user
received an answer. Its rate is reported on its own.
"""

from __future__ import annotations

from dataclasses import dataclass

VERDICTS = ("PASS", "PARTIAL", "ABSTAIN")


@dataclass(frozen=True)
class TwoByTwo:
    answered_answerable: int
    abstained_answerable: int  # over-abstention
    answered_unanswerable: int  # false answer, the worst outcome
    abstained_unanswerable: int
    partial: int = 0  # PARTIAL verdicts, already counted as answered


def two_by_two(rows: list[tuple[bool, str]]) -> TwoByTwo:
    """`rows`: (expected_abstain, verdict) per item."""
    c = {"aa": 0, "ba": 0, "au": 0, "bu": 0}
    partial = 0
    for expected, verdict in rows:
        if verdict not in VERDICTS:
            raise ValueError(f"unknown verdict {verdict!r}")
        partial += verdict == "PARTIAL"
        abstained = verdict == "ABSTAIN"
        c[("b" if abstained else "a") + ("u" if expected else "a")] += 1
    return TwoByTwo(c["aa"], c["ba"], c["au"], c["bu"], partial)


def _div(a: int, b: int) -> float | None:
    return a / b if b else None


def rates(t: TwoByTwo) -> dict:
    unanswerable = t.answered_unanswerable + t.abstained_unanswerable
    answerable = t.answered_answerable + t.abstained_answerable
    abstained = t.abstained_unanswerable + t.abstained_answerable
    precision = _div(t.abstained_unanswerable, abstained)
    recall = _div(t.abstained_unanswerable, unanswerable)
    f1 = None
    if precision is not None and recall is not None and precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    total = unanswerable + answerable
    return {
        "partial_rate": _div(t.partial, total),
        "false_answer_rate": _div(t.answered_unanswerable, unanswerable),
        "over_abstention_rate": _div(t.abstained_answerable, answerable),
        "abstention_precision": precision,
        "abstention_recall": recall,
        "abstention_f1": f1,
    }
