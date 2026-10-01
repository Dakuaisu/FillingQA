"""Phase 2 step 4: prove the search indexes are used and return the right rows.

python -m scripts.check_indexes

On a table this small the planner prefers a sequential scan, so
`enable_seqscan` is turned off for this session only: the point is to show the indexes CAN serve
these query shapes, not that the planner picks them on a tiny table.

1. EXPLAIN a `<=>` ORDER BY ... LIMIT query -> chunks_hnsw.
2. EXPLAIN a `@@` full-text query -> chunks_tsv.
3. 20 chunks, spread across the table, each queried with its own vector through
   the HNSW index: the chunk must come back at cosine distance 0. Some chunks
   share identical text (and so identical vectors), so "itself" is checked among
   all distance-0 results, not by rank alone.
"""

from __future__ import annotations

import re

from api.db import connect

SAMPLE = 20
_VECTOR_LITERAL = re.compile(r"'\[[^\]]*\]'::vector")


def _plan_line(line: str) -> str:
    """The plan with the 768-float query vector elided, so the operators show."""
    return _VECTOR_LITERAL.sub("'[...]'::vector", line)


def main() -> None:
    with connect() as conn:
        conn.execute("SET enable_seqscan = off")
        probe = conn.execute(
            "SELECT embedding::text FROM chunks ORDER BY chunk_id LIMIT 1"
        ).fetchone()[0]

        plan = conn.execute(
            "EXPLAIN SELECT chunk_id FROM chunks ORDER BY embedding <=> %s::vector LIMIT 5",
            (probe,),
        ).fetchall()
        print("EXPLAIN <=> ORDER BY LIMIT:")
        for (line,) in plan:
            print("   ", _plan_line(line))

        plan = conn.execute(
            "EXPLAIN SELECT chunk_id FROM chunks WHERE tsv @@ plainto_tsquery('english', %s)",
            ("inventory valuation",),
        ).fetchall()
        print("EXPLAIN @@:")
        for (line,) in plan:
            print("   ", line)
        hits = conn.execute(
            "SELECT count(*) FROM chunks WHERE tsv @@ plainto_tsquery('english', %s)",
            ("inventory valuation",),
        ).fetchone()[0]
        print(f"    rows matching 'inventory valuation': {hits}")

        total = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        step = max(1, total // SAMPLE)
        sample = conn.execute(
            """
            SELECT chunk_id, embedding::text FROM (
                SELECT chunk_id, embedding, row_number() OVER (ORDER BY chunk_id) AS n
                  FROM chunks
            ) t WHERE (n - 1) %% %s = 0 ORDER BY chunk_id LIMIT %s
            """,
            (step, SAMPLE),
        ).fetchall()
        found = 0
        print(f"self-retrieval through chunks_hnsw ({len(sample)} chunks):")
        for chunk_id, vector in sample:
            rows = conn.execute(
                """
                SELECT chunk_id, embedding <=> %s::vector AS distance
                  FROM chunks ORDER BY embedding <=> %s::vector LIMIT 5
                """,
                (vector, vector),
            ).fetchall()
            at_zero = [cid for cid, d in rows if d < 1e-6]
            ok = chunk_id in at_zero
            found += ok
            print(
                f"    {chunk_id:40} top-1 distance {rows[0][1]:.2e}  "
                f"distance-0 results {len(at_zero)}  {'self found' if ok else 'SELF MISSING'}"
            )
        print(f"self found at distance 0: {found} of {len(sample)}")


if __name__ == "__main__":
    main()
