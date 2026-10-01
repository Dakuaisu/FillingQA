"""Dense retrieval for the Phase 2 naive baseline (PRD 14): `<=>` over all
chunks, top-k, through chunks_hnsw. No hybrid, no rerank, no filter.

The question is embedded with the same pinned model and revision as the chunks
and exactly as they were: normalized, no instruction prefix (TRADEOFFS, Phase 2
baseline). A question longer than the model's input fails rather than being
truncated, as a chunk would.
"""

from __future__ import annotations

from dataclasses import dataclass

import psycopg

from api.index.embed import EmbeddingCheckError, vector_literal


@dataclass
class Retrieved:
    chunk_id: str
    distance: float
    text: str


def embed_question(model, cfg: dict, question: str) -> str:
    n = len(model.tokenizer(question, truncation=False)["input_ids"])
    if n > cfg["max_seq_length"]:
        raise EmbeddingCheckError(
            f"question is {n} tokens, over max_seq_length {cfg['max_seq_length']}"
        )
    vector = model.encode([question], normalize_embeddings=True, convert_to_numpy=True)[0]
    return vector_literal(vector)


_QUERY = """
    SELECT chunk_id, embedding <=> %(q)s::vector AS distance, text
      FROM chunks
     ORDER BY embedding <=> %(q)s::vector
     LIMIT %(k)s
"""


def dense_top_k(conn: psycopg.Connection, query_vector: str, k: int) -> tuple[list[Retrieved], str]:
    """Top-k chunks by cosine distance, and the plan node that served them.

    On a corpus this small the planner prefers an exact sequential scan; the
    baseline is specified "through chunks_hnsw", so seqscan is switched off for
    this transaction only.
    """
    with conn.transaction():
        conn.execute("SET LOCAL enable_seqscan = off")
        plan = conn.execute("EXPLAIN " + _QUERY, {"q": query_vector, "k": k}).fetchall()
        rows = conn.execute(_QUERY, {"q": query_vector, "k": k}).fetchall()
    node = next((line for (line,) in plan if "Scan" in line), "").strip()
    return [Retrieved(cid, float(d), text) for cid, d, text in rows], node
