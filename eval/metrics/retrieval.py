"""Retrieval metrics over alternative evidence sets (PRD 11.2; F-77 decided). Pure.

`retrieved` is the ordered list of chunk ids the metric is measured on (F-13:
post-fusion, pre-rerank); `sets` is the item's `gold_evidence_sets`. An item
with no evidence set (an abstain item) has no retrieval score: every function
returns None for it.
"""

from __future__ import annotations

from math import log2


def _top(retrieved: list[str], k: int) -> list[str]:
    if k < 1:
        raise ValueError("k must be at least 1")
    return retrieved[:k]


def sufficiency_at_k(retrieved: list[str], sets: list[list[str]], k: int) -> bool | None:
    """Some evidence set is fully covered in the top k."""
    if not sets:
        return None
    top = set(_top(retrieved, k))
    return any(set(es) <= top for es in sets)


def recall_at_k(retrieved: list[str], sets: list[list[str]], k: int) -> float | None:
    """Best per-set coverage: max over sets of |top k ∩ es| / |es|."""
    if not sets:
        return None
    top = set(_top(retrieved, k))
    return max(len(top & set(es)) / len(set(es)) for es in sets)


def precision_at_k(retrieved: list[str], sets: list[list[str]], k: int) -> float | None:
    """|top k ∩ union of sets| / k."""
    if not sets:
        return None
    union = {c for es in sets for c in es}
    return len(set(_top(retrieved, k)) & union) / k


def mrr(retrieved: list[str], sets: list[list[str]]) -> float | None:
    """1 / rank of the first retrieved chunk in any set; 0 if none is retrieved."""
    if not sets:
        return None
    union = {c for es in sets for c in es}
    return next((1 / rank for rank, c in enumerate(retrieved, start=1) if c in union), 0.0)


def _ndcg_one(top: list[str], es: list[str], k: int) -> float:
    gold, seen = set(es), set()
    dcg = 0.0
    for i, c in enumerate(top, start=1):
        if c in gold and c not in seen:
            dcg += 1 / log2(i + 1)
            seen.add(c)
    ideal = sum(1 / log2(i + 1) for i in range(1, min(len(gold), k) + 1))
    return dcg / ideal


def ndcg_at_k(retrieved: list[str], sets: list[list[str]], k: int) -> float | None:
    """Per-set nDCG@k with IDCG over min(|set|, k), each chunk counted once; the item
    takes the best set (F-77)."""
    if not sets:
        return None
    top = _top(retrieved, k)
    return max(_ndcg_one(top, es, k) for es in sets)
