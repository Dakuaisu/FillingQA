"""PRD 7.5's NLI gate arithmetic. Inline data; the model itself is not loaded."""

from __future__ import annotations

import pytest

from api.verify.nli import auc, youden_threshold


def test_auc_counts_ties_half_and_needs_both_classes():
    assert auc([0.9, 0.8, 0.1], [True, True, False]) == 1.0
    assert auc([0.5, 0.5], [True, False]) == 0.5
    assert auc([0.2, 0.9], [True, False]) == 0.0
    with pytest.raises(ValueError):
        auc([0.9], [True])


def test_youden_threshold_is_the_best_cut_on_the_labels():
    scores = [0.95, 0.9, 0.7, 0.6, 0.3, 0.1]
    labels = [True, True, True, False, False, False]
    assert youden_threshold(scores, labels) == 0.7
