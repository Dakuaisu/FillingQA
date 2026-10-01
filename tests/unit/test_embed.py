"""Embedding pipeline checks. No network: the model is a stand-in built on the
vendored tokenizer, so these test the assertions, not the encoder."""

from __future__ import annotations

import pytest

from api.chunk.tokens import sequence_length, tokenizer
from api.config import embedding
from api.index.embed import EmbeddingCheckError, check_lengths, vector_literal


class StandInModel:
    """Exposes what check_lengths reads from a SentenceTransformer."""

    def __init__(self, max_seq_length: int = 512, dim: int = 768) -> None:
        self.max_seq_length = max_seq_length
        self._dim = dim

    def get_embedding_dimension(self) -> int:
        return self._dim

    @staticmethod
    def tokenizer(text: str, truncation: bool, add_special_tokens: bool) -> dict:
        assert truncation is False  # counting must never be capped
        return {"input_ids": tokenizer().encode(text, add_special_tokens=add_special_tokens).ids}


CFG = embedding()
TEXT = "[Apple Inc. (AAPL) | 10-K | FY2025 | Item 8: Financial Statements]\nTotal net sales 416,161"


def test_matching_counts_pass():
    out = check_lengths(StandInModel(), CFG, [("c1", TEXT, sequence_length(TEXT))])
    assert out["token_count_mismatches"] == 0 and out["chunks_checked"] == 1


def test_a_stored_count_the_model_disagrees_with_fails():
    with pytest.raises(EmbeddingCheckError, match="token counts differ"):
        check_lengths(StandInModel(), CFG, [("c1", TEXT, sequence_length(TEXT) - 1)])


def test_a_chunk_over_the_limit_fails_rather_than_truncates():
    long = "word " * 600
    with pytest.raises(EmbeddingCheckError, match="exceed max_seq_length"):
        check_lengths(StandInModel(), CFG, [("c1", long, sequence_length(long))])


def test_config_and_model_must_agree_on_length_and_dimension():
    with pytest.raises(EmbeddingCheckError, match="max_seq_length"):
        check_lengths(StandInModel(max_seq_length=256), CFG, [])
    with pytest.raises(EmbeddingCheckError, match="dimension"):
        check_lengths(StandInModel(dim=384), CFG, [])


def test_vector_literal_is_pgvector_text_at_full_precision():
    assert vector_literal([0.1, -2.5e-05, 1]) == "[0.1,-2.5e-05,1.0]"
