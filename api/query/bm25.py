"""Okapi BM25 over the chunks, self-written (TRADEOFFS: BM25 sparse retrieval; F-108).

score(d, q) = sum over unique query terms t of
    idf(t) * tf(t, d) * (k1 + 1) / (tf(t, d) + k1 * (1 - b + b * |d| / avgdl))
idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))      (never negative)

The indexed text is the chunk's stored `text`, context header included, so
tickers, Item codes and period labels match. The index is cached under the data
directory keyed on `chunker_version` plus a hash of every chunk's text; a stale
index is rebuilt, and an index used against another key is refused.
"""

from __future__ import annotations

import hashlib
import math
import pickle
import re
from collections import Counter
from dataclasses import dataclass, field

# Tokens, in order of preference: a figure with thousands separators ("7,286",
# "1,434.5") kept as one token without commas; a hyphen-joined alphanumeric run
# ("10-q", "8-k", "non-gaap"); a plain alphanumeric run ("7a", "fy2024", "aapl").
# No stemming: financial line items ("income" / "incomes", "loss" / "losses")
# are matched literally, and a stemmer would be a dependency with its own
# version to pin.
TOKEN = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|[a-z0-9]+(?:-[a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return [t.replace(",", "") for t in TOKEN.findall(text.lower())]


def corpus_key(chunker_version: str, rows: list[tuple[str, str]]) -> str:
    """`rows`: (chunk_id, text) for every indexed chunk."""
    h = hashlib.sha256(chunker_version.encode())
    for cid, text in sorted(rows):
        h.update(cid.encode() + b"\0" + text.encode() + b"\0")
    return h.hexdigest()


class StaleIndexError(RuntimeError):
    """The index was built over another chunk set or chunker version."""


@dataclass
class Index:
    key: str
    k1: float
    b: float
    ids: list[str]
    lengths: list[int]
    avgdl: float
    postings: dict[str, list[tuple[int, int]]] = field(repr=False)

    @property
    def n(self) -> int:
        return len(self.ids)

    def idf(self, term: str) -> float:
        df = len(self.postings.get(term, ()))
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def check(self, key: str) -> None:
        if key != self.key:
            raise StaleIndexError("BM25 index was built over another chunk set; rebuild it")

    def search(self, question: str, k: int) -> list[tuple[str, float]]:
        """Top-k (chunk_id, score), score descending, then chunk_id; zero scores dropped."""
        scores: dict[int, float] = {}
        for term in set(tokenize(question)):
            plist = self.postings.get(term)
            if not plist:
                continue
            w = self.idf(term)
            for doc, tf in plist:
                norm = self.k1 * (1 - self.b + self.b * self.lengths[doc] / self.avgdl)
                scores[doc] = scores.get(doc, 0.0) + w * tf * (self.k1 + 1) / (tf + norm)
        ranked = sorted(scores.items(), key=lambda x: (-x[1], self.ids[x[0]]))
        return [(self.ids[d], s) for d, s in ranked[:k] if s > 0]


def build(rows: list[tuple[str, str]], key: str, k1: float, b: float) -> Index:
    rows = sorted(rows)
    postings: dict[str, list[tuple[int, int]]] = {}
    lengths = []
    for doc, (_, text) in enumerate(rows):
        toks = tokenize(text)
        lengths.append(len(toks))
        for term, tf in Counter(toks).items():
            postings.setdefault(term, []).append((doc, tf))
    avgdl = sum(lengths) / len(lengths) if lengths else 0.0
    return Index(key, k1, b, [cid for cid, _ in rows], lengths, avgdl, postings)


def load_or_build(path, rows: list[tuple[str, str]], chunker_version: str, k1: float, b: float):
    """The cached index if its key, k1 and b match; otherwise a fresh one, cached.
    Returns (index, rebuilt)."""
    key = corpus_key(chunker_version, rows)
    if path.exists():
        with path.open("rb") as fh:
            idx = pickle.load(fh)
        if idx.key == key and idx.k1 == k1 and idx.b == b:
            return idx, False
    idx = build(rows, key, k1, b)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        pickle.dump(idx, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return idx, True
