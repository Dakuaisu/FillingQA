"""NLI entailment for prose claims (PRD 7.5). Decisions in TRADEOFFS ("NLI for
prose claims and its AUC gate"). The model loads once; scoring is batched."""

from __future__ import annotations

MODEL = "cross-encoder/nli-deberta-v3-base"
REVISION = "6c749ce3425cd33b46d187e45b92bbf96ee12ec7"
MAX_TOKENS = 512


class Nli:
    def __init__(self, device: str | None = None):
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(MODEL, revision=REVISION, device=device)
        labels = {v.lower(): int(k) for k, v in self.model.model.config.id2label.items()}
        self.entail = labels["entailment"]

    def tokens(self, premise: str, hypothesis: str) -> int:
        return len(self.model.tokenizer(premise, hypothesis, truncation=False)["input_ids"])

    def score(self, pairs: list[tuple[str, str]]) -> list[float]:
        """Entailment probability per (premise chunk, hypothesis claim)."""
        if not pairs:
            return []
        probs = self.model.predict(pairs, apply_softmax=True)
        return [float(p[self.entail]) for p in probs]


def auc(scores: list[float], labels: list[bool]) -> float:
    """Mann-Whitney AUC: the chance a supporting pair outscores a non-supporting
    one, ties counting half."""
    pos = [s for s, y in zip(scores, labels, strict=True) if y]
    neg = [s for s, y in zip(scores, labels, strict=True) if not y]
    if not pos or not neg:
        raise ValueError("AUC needs both supporting and non-supporting pairs")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def youden_threshold(scores: list[float], labels: list[bool]) -> float:
    """The score cut maximizing sensitivity + specificity - 1 (ties: the lowest
    cut), predicting support at score >= cut."""
    pos, neg = sum(labels), len(labels) - sum(labels)
    best, cut = -2.0, None
    for t in sorted(set(scores)):
        tp = sum(s >= t and y for s, y in zip(scores, labels, strict=True))
        tn = sum(s < t and not y for s, y in zip(scores, labels, strict=True))
        j = tp / pos + tn / neg - 1
        if j > best:
            best, cut = j, t
    return cut
