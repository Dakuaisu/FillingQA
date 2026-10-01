"""Cohen's kappa between the owner's labels and the judge's (PRD 11.3). Pure.

Unweighted, over the 1-5 rubric categories. kappa < 0.6 marks the judge
unreliable and every metric built on it suspect (PRD 11.3).
"""

from __future__ import annotations

from collections import Counter

RELIABLE = 0.6


def cohens_kappa(a: list[int], b: list[int]) -> float | None:
    """None when undefined (no pairs, or chance agreement is 1: both raters used one
    and the same category throughout)."""
    if len(a) != len(b):
        raise ValueError(f"{len(a)} labels against {len(b)}")
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1:
        return None
    return (po - pe) / (1 - pe)
