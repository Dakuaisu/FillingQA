"""Embedding pipeline: PRD 6.4 and Phase 2 step 3.

python -m api.index.embed

Batched, resumable, content-hash cached. The model is named only in
api/config.yaml (`embedding.model` at `embedding.revision`).

Two checks run before anything is written, so that "the chunker's count and the
model's truncation agree" is verified rather than claimed:

1. the loaded model's `max_seq_length` equals the config's;
2. the model's own tokenizer, truncation off, reproduces every stored
   `chunks.token_count`. Any chunk over `max_seq_length` fails the run -- a vector
   of a truncated chunk would represent text the chunk does not end with.

`text` is embedded with its context header (PRD 6.4), normalized for cosine.
Passages get no instruction prefix; bge's query prefix belongs to query time.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import psycopg

from api.config import embedding
from api.db import connect


class EmbeddingCheckError(RuntimeError):
    """The model would not see the text the chunker measured."""


@dataclass
class EmbedReport:
    ticker: str
    accession: str
    skipped: int = 0  # already had an embedding
    from_cache: int = 0
    embedded: int = 0  # newly encoded
    seconds: float = 0.0


def vector_literal(values) -> str:
    """pgvector's text form, `[0.1,0.2,...]`; full float precision via repr."""
    return "[" + ",".join(repr(float(v)) for v in values) + "]"


def load_model():
    # Imported here: torch is heavy, and nothing else in the package needs it.
    from sentence_transformers import SentenceTransformer

    cfg = embedding()
    model = SentenceTransformer(cfg["model"], revision=cfg["revision"])
    return model, cfg


def check_lengths(model, cfg: dict, rows: list[tuple[str, str, int]]) -> dict:
    """Assertions 1 and 2. `rows` is (chunk_id, text, token_count)."""
    dim = model.get_embedding_dimension()
    if dim != cfg["dim"]:
        raise EmbeddingCheckError(f"model dimension {dim} != config {cfg['dim']}")
    if model.max_seq_length != cfg["max_seq_length"]:
        raise EmbeddingCheckError(
            f"model max_seq_length {model.max_seq_length} != config {cfg['max_seq_length']}"
        )
    tokenizer = model.tokenizer
    mismatched, over = [], []
    for chunk_id, text, stored in rows:
        n = len(tokenizer(text, truncation=False, add_special_tokens=True)["input_ids"])
        if n != stored:
            mismatched.append((chunk_id, stored, n))
        if n > cfg["max_seq_length"]:
            over.append((chunk_id, n))
    if mismatched:
        raise EmbeddingCheckError(f"{len(mismatched)} token counts differ, e.g. {mismatched[:3]}")
    if over:
        raise EmbeddingCheckError(f"{len(over)} chunks exceed max_seq_length, e.g. {over[:3]}")
    return {
        "dim": dim,
        "max_seq_length": model.max_seq_length,
        "chunks_checked": len(rows),
        "token_count_mismatches": len(mismatched),
        "over_max_seq_length": len(over),
    }


_FILL_FROM_CACHE = """
    UPDATE chunks c SET embedding = e.embedding
      FROM embedding_cache e
     WHERE c.accession = %s AND c.embedding IS NULL
       AND e.content_hash = c.content_hash AND e.model = %s AND e.revision = %s
"""


def embed_filing(
    conn: psycopg.Connection, model, cfg: dict, ticker: str, accession: str
) -> EmbedReport:
    report = EmbedReport(ticker, accession)
    started = time.monotonic()
    key = (cfg["model"], cfg["revision"])

    report.skipped = conn.execute(
        "SELECT count(*) FROM chunks WHERE accession = %s AND embedding IS NOT NULL",
        (accession,),
    ).fetchone()[0]

    with conn.transaction():
        report.from_cache = conn.execute(_FILL_FROM_CACHE, (accession, *key)).rowcount

    pending = conn.execute(
        """
        SELECT DISTINCT content_hash, text FROM chunks
         WHERE accession = %s AND embedding IS NULL ORDER BY content_hash
        """,
        (accession,),
    ).fetchall()
    size = cfg["batch_size"]
    for i in range(0, len(pending), size):
        batch = pending[i : i + size]
        vectors = model.encode(
            [text for _, text in batch],
            batch_size=size,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        with conn.transaction():
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO embedding_cache (content_hash, model, revision, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    ON CONFLICT DO NOTHING
                    """,
                    [
                        (h, *key, vector_literal(v))
                        for (h, _), v in zip(batch, vectors, strict=True)
                    ],
                )
            report.embedded += conn.execute(_FILL_FROM_CACHE, (accession, *key)).rowcount

    report.seconds = time.monotonic() - started
    return report


def main() -> None:
    model, cfg = load_model()
    print(f"model {cfg['model']}@{cfg['revision'][:12]} device {model.device}")
    with connect() as conn:
        rows = conn.execute("SELECT chunk_id, text, token_count FROM chunks").fetchall()
        print("checks:", check_lengths(model, cfg, rows))
        filings = conn.execute(
            """
            SELECT DISTINCT c.ticker, ch.accession, f.filing_date
              FROM chunks ch JOIN filings f USING (accession) JOIN companies c ON c.cik = f.cik
             ORDER BY c.ticker, f.filing_date
            """
        ).fetchall()
        conn.commit()
        header = ("ticker", "accession", "embedded", "cache", "skipped", "seconds")
        print("{:6} {:22} {:>8} {:>5} {:>7} {:>7}".format(*header))
        for ticker, accession, _ in filings:
            r = embed_filing(conn, model, cfg, ticker, accession)
            print(
                f"{r.ticker:6} {r.accession:22} {r.embedded:8} {r.from_cache:5} "
                f"{r.skipped:7} {r.seconds:7.1f}"
            )
        missing = conn.execute("SELECT count(*) FROM chunks WHERE embedding IS NULL").fetchone()[0]
        print(f"chunks with embedding IS NULL: {missing}")


if __name__ == "__main__":
    main()
