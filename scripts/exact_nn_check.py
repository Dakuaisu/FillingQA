"""One-off measurement for F-109: exact nearest neighbours vs HNSW at the pinned
`retrieval.hnsw_ef_search`, for every candidate question. No model call.

python -m scripts.exact_nn_check

Exact search is a sequential scan of every stored chunk embedding (cosine `<=>`
with index scans switched off). Prints how many top-k lists differ.
"""

from __future__ import annotations

import json

from api.config import REPO_ROOT, eval_run, retrieval
from api.db import connect
from api.index.embed import load_model
from api.query.retrieve import dense_top_k, embed_question

DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
EXACT = "SELECT chunk_id FROM chunks ORDER BY embedding <=> %(q)s::vector, chunk_id LIMIT %(k)s"


def main() -> None:
    cfg, k = retrieval(), eval_run()["k"]
    items = [
        json.loads(x) for p in DATASETS for x in p.read_text(encoding="utf-8").split("\n") if x
    ]
    model, emb = load_model()
    differ, overlap = [], []
    with connect() as conn:
        n = conn.execute("SELECT count(embedding) FROM chunks").fetchone()[0]
        for it in items:
            vec = embed_question(model, emb, it["question"])
            approx = [r.chunk_id for r in dense_top_k(conn, vec, k, cfg["hnsw_ef_search"])[0]]
            with conn.transaction():
                conn.execute("SET LOCAL enable_indexscan = off")
                conn.execute("SET LOCAL enable_bitmapscan = off")
                exact = [r[0] for r in conn.execute(EXACT, {"q": vec, "k": k}).fetchall()]
            if approx != exact:
                differ.append(it["item_id"])
                overlap.append(len(set(approx) & set(exact)))
    print(f"vectors {n}; questions {len(items)}; k {k}; hnsw.ef_search {cfg['hnsw_ef_search']}")
    print(f"top-{k} lists differing from exact search: {len(differ)} "
          f"(order or membership); membership overlap among them: {sorted(overlap)}")  # fmt: skip
    print(f"  {differ}")


if __name__ == "__main__":
    main()
