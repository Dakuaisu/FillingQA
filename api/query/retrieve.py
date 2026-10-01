"""Retrieval. Dense (Phase 2 baseline): `<=>` over all chunks through chunks_hnsw.
Sparse: Postgres full-text over `chunks.tsv` ranked by `ts_rank_cd` (PRD 6.4).
Hybrid (PRD 7.2): dense top-k_dense and sparse top-k_sparse fused by weighted
Reciprocal Rank Fusion; the fused list is the pre-rerank list (F-13).

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


def dense_top_k(
    conn: psycopg.Connection, query_vector: str, k: int, ef_search: int
) -> tuple[list[Retrieved], str]:
    """Top-k chunks by cosine distance, and the plan node that served them.

    On a corpus this small the planner prefers an exact sequential scan; the
    baseline is specified "through chunks_hnsw", so seqscan is switched off for
    this transaction only. `ef_search` is set on every query (config
    `retrieval.hnsw_ef_search`, F-109): HNSW is approximate and its result
    depends on it.
    """
    if ef_search < k:
        raise ValueError(f"hnsw.ef_search {ef_search} < k {k}: HNSW returns at most ef_search rows")
    with conn.transaction():
        conn.execute("SET LOCAL enable_seqscan = off")
        conn.execute(f"SET LOCAL hnsw.ef_search = {int(ef_search)}")  # pinned (F-109)
        plan = conn.execute("EXPLAIN " + _QUERY, {"q": query_vector, "k": k}).fetchall()
        rows = conn.execute(_QUERY, {"q": query_vector, "k": k}).fetchall()
    node = next((line for (line,) in plan if "Scan" in line), "").strip()
    return [Retrieved(cid, float(d), text) for cid, d, text in rows], node


# The question's lexemes OR-ed: an AND of every term of a natural-language question
# rarely matches a chunk; ts_rank_cd then orders by coverage and proximity.
_SPARSE = """
    WITH q AS (
        SELECT to_tsquery('english', string_agg(quote_literal(lexeme), ' | ')) AS query
          FROM unnest(to_tsvector('english', %(question)s))
    )
    SELECT c.chunk_id, ts_rank_cd(c.tsv, q.query) AS rank, c.text
      FROM chunks c, q
     WHERE q.query IS NOT NULL AND c.tsv @@ q.query
     ORDER BY rank DESC, c.chunk_id
     LIMIT %(k)s
"""


def sparse_top_k(conn: psycopg.Connection, question: str, k: int) -> list[Retrieved]:
    """Top-k chunks by `ts_rank_cd` (higher is better; stored in `distance` as -rank)."""
    rows = conn.execute(_SPARSE, {"question": question, "k": k}).fetchall()
    return [Retrieved(cid, -float(r), text) for cid, r, text in rows]


def rrf_fuse(rankings: list[list[str]], weights: list[float], k_const: int) -> list[str]:
    """Weighted Reciprocal Rank Fusion (PRD 7.2): score(d) = sum_i w_i / (k + rank_i(d)),
    ranks from 1. Ties go to the better best rank, then the smaller chunk id."""
    if len(rankings) != len(weights):
        raise ValueError(f"{len(rankings)} rankings for {len(weights)} weights")
    score: dict[str, float] = {}
    best: dict[str, int] = {}
    for ranking, w in zip(rankings, weights, strict=True):
        seen = set()
        for rank, cid in enumerate(ranking, start=1):
            if cid in seen:
                continue
            seen.add(cid)
            score[cid] = score.get(cid, 0.0) + w / (k_const + rank)
            best[cid] = min(best.get(cid, rank), rank)
    return sorted(score, key=lambda c: (-score[c], best[c], c))


def load_bm25(conn: psycopg.Connection, sparse_cfg: dict):
    """The BM25 index over every stored chunk's text (header included), from the
    cache when its key (chunker_version + chunk texts) and parameters match.
    Returns (index, rebuilt)."""
    from api.chunk.store import chunker_version
    from api.config import data_dir
    from api.query import bm25

    rows = conn.execute("SELECT chunk_id, text FROM chunks ORDER BY chunk_id").fetchall()
    path = data_dir() / "cache" / f"bm25_k1{sparse_cfg['k1']}_b{sparse_cfg['b']}.pkl"
    return bm25.load_or_build(path, rows, chunker_version(), sparse_cfg["k1"], sparse_cfg["b"])


def sparse(
    conn: psycopg.Connection, question: str, k: int, sparse_cfg: dict, index=None
) -> list[str]:
    """Sparse top-k chunk ids by the configured backend: `bm25` (needs `index`) or
    `postgres_fts` (the Phase 2 `ts_rank_cd` artifact, F-108)."""
    backend = sparse_cfg["backend"]
    if backend == "bm25":
        if index is None:
            raise ValueError("the bm25 backend needs a loaded index")
        return [cid for cid, _ in index.search(question, k)]
    if backend == "postgres_fts":
        return [r.chunk_id for r in sparse_top_k(conn, question, k)]
    raise ValueError(f"unknown sparse backend {backend!r}")


def hybrid_top_k(
    conn: psycopg.Connection, query_vector: str, question: str, cfg: dict, index=None
) -> list[str]:
    """The fused pre-rerank list (chunk ids), length up to max(k_dense, k_sparse)."""
    dense, _ = dense_top_k(conn, query_vector, cfg["k_dense"], cfg["hnsw_ef_search"])
    sp = sparse(conn, question, cfg["k_sparse"], cfg["sparse"], index)
    w = cfg["weights"]
    fused = rrf_fuse([[r.chunk_id for r in dense], sp], [w["dense"], w["sparse"]], cfg["rrf_k"])
    return fused[: max(cfg["k_dense"], cfg["k_sparse"])]


_DENSE_FILTERED = """
    SELECT chunk_id FROM chunks WHERE chunk_id = ANY(%(ids)s)
     ORDER BY embedding <=> %(q)s::vector, chunk_id LIMIT %(k)s
"""


def dense_filtered_top_k(
    conn: psycopg.Connection, query_vector: str, k: int, allowed: set[str]
) -> list[str]:
    """Exact nearest neighbours among the allowed chunks (sequential scan): a
    filtered HNSW scan can return fewer than k rows, and a filtered slice is small."""
    with conn.transaction():
        conn.execute("SET LOCAL enable_indexscan = off")
        conn.execute("SET LOCAL enable_bitmapscan = off")
        rows = conn.execute(_DENSE_FILTERED, {"ids": sorted(allowed), "q": query_vector, "k": k})
        return [r[0] for r in rows.fetchall()]
