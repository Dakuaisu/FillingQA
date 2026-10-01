"""Token counting with the embedding model's own tokenizer (F-53).

The vendored tokenizer.json is the file sentence-transformers loads for the
pinned model revision, so a count here is the sequence length the model sees --
and a chunk that fits here is never silently truncated at embedding.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache

from tokenizers import Tokenizer

from api.config import REPO_ROOT, ConfigError, embedding


@lru_cache(maxsize=1)
def tokenizer() -> Tokenizer:
    cfg = embedding()
    path = REPO_ROOT / cfg["tokenizer_file"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != cfg["tokenizer_sha256"]:
        raise ConfigError(f"{path} sha256 {actual} != pinned {cfg['tokenizer_sha256']}")
    tok = Tokenizer.from_file(str(path))
    # Counting must see the full length; truncation is what F-53 exists to catch.
    tok.no_truncation()
    tok.no_padding()
    return tok


def count_tokens(text: str) -> int:
    """Tokens in a piece of text, without [CLS]/[SEP]: pieces add up."""
    return len(tokenizer().encode(text, add_special_tokens=False).ids)


def sequence_length(text: str) -> int:
    """The model's input length for `text`, special tokens included."""
    return len(tokenizer().encode(text).ids)
