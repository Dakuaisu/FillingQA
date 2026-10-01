"""Which lists an eval run stores and what the generator receives, per pipeline
(PRD 11.6 configs; F-13, F-61). Pure.

- config_1_dense: dense top-`retrieve_depth`; the generator gets `baseline.top_k`.
- config_3_hybrid: the RRF-fused list; the generator gets its top-n.
- config_4_rerank: the fused list reranked; over the timeout, RRF order instead
  (PRD 7.3); the score floor applied; an empty list after the floor abstains
  without calling the generator.
"""

from __future__ import annotations

from api.query.rerank import apply_floor, top_n_for

PIPELINES = ("config_1_dense", "config_3_hybrid", "config_4_rerank")


def context_for(
    pipeline: str,
    *,
    dense: list[str],
    fused: list[str],
    reranked: list[tuple[str, float]] | None,
    rerank_seconds: float | None,
    rerank_cfg: dict,
    question_type: str,
    baseline_top_k: int,
) -> dict:
    """{retrieved (pre-rerank), retrieved_post_rerank, generator_input, fell_back, abstain}."""
    if pipeline == "config_1_dense":
        return {"retrieved": dense, "retrieved_post_rerank": None,
                "generator_input": dense[:baseline_top_k],
                "fell_back": False, "abstain": False}  # fmt: skip
    top = top_n_for(question_type, rerank_cfg)
    if pipeline == "config_3_hybrid":
        return {"retrieved": fused, "retrieved_post_rerank": None,
                "generator_input": fused[:top], "fell_back": False, "abstain": False}  # fmt: skip
    if pipeline != "config_4_rerank":
        raise ValueError(f"unknown pipeline {pipeline!r}; one of {PIPELINES}")
    if reranked is None or rerank_seconds is None:
        raise ValueError("config_4_rerank needs the reranked list and its latency")
    fell_back = rerank_seconds * 1000 > rerank_cfg["timeout_ms"]
    if fell_back:
        post = fused[:top]
    else:
        post = [c for c, _ in apply_floor(reranked, rerank_cfg["score_floor"])[:top]]
    return {"retrieved": fused, "retrieved_post_rerank": post, "generator_input": post,
            "fell_back": fell_back, "abstain": not post}  # fmt: skip
