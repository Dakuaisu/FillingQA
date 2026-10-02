"""Which lists an eval run stores and what the generator receives, per pipeline
(PRD 11.6 configs; F-13, F-61). Pure.

- config_1_dense: dense top-`retrieve_depth`; the generator gets `baseline.top_k`.
- config_3_hybrid: the RRF-fused list; the generator gets its top-n.
- config_4_rerank: the fused list reranked; over the timeout, RRF order instead
  (PRD 7.3); the score floor applied; an empty list after the floor abstains
  without calling the generator.
- config_4_routed: Config 4 behind PRD 7.1's router (Config 8's component; 5-7
  not built): metadata filters, and per intent the generator tier, k per query,
  rerank top-n and sub-queries (`router.budgets`).
"""

from __future__ import annotations

from api.query.rerank import apply_floor, top_n_for

PIPELINES = ("config_1_dense", "config_3_hybrid", "config_4_rerank", "config_4_routed")


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


def depths(pipeline: str, *, retrieve_depth: int, retrieval_cfg: dict, rerank_cfg: dict,
           baseline_top_k: int, budgets: dict | None = None) -> dict:  # fmt: skip
    """What a run stores and feeds the generator, from config: the length of
    `retrieved` and the generator's top-k (per question type after fusion; per
    intent when routed)."""
    if pipeline == "config_1_dense":
        return {"retrieve_depth": retrieve_depth, "generator_top_k": baseline_top_k}
    if pipeline == "config_4_routed":
        b = budgets or {}
        return {"retrieve_depth": {i: x["k"] * x["sub_queries"] for i, x in b.items()},
                "generator_top_k": {i: x["top_n"] for i, x in b.items()}}  # fmt: skip
    if pipeline not in PIPELINES:
        raise ValueError(f"unknown pipeline {pipeline!r}; one of {PIPELINES}")
    return {"retrieve_depth": max(retrieval_cfg["k_dense"], retrieval_cfg["k_sparse"]),
            "generator_top_k": {"default": rerank_cfg["top_n"],
                                "synthesis": rerank_cfg["top_n_synthesis"]}}  # fmt: skip


def depth_disagreements(meta: dict, results: list[dict], items: dict) -> list[str]:
    """Item ids whose stored lists contradict the run meta: `retrieved` not of
    length retrieve_depth (routed: longer than it, since a filter may admit fewer
    chunks), or a generator input longer than its top-k, or shorter where only the
    score floor may shorten it. Routed `unsupported` items must have neither list."""
    depth, top = meta["retrieve_depth"], meta["generator_top_k"]
    pipeline = meta.get("pipeline")
    routed = pipeline == "config_4_routed"
    out = []
    for r in results:
        n = len(r.get("generator_input") or [])
        if routed:
            if r.get("intent") == "unsupported":
                if r["retrieved"] or n:
                    out.append(r["item_id"])
                continue
            key = r.get("intent") or "unrouted"
            want, k = depth[key], top[key]
            bad_len = len(r["retrieved"]) > want
            floor_may_shorten = True
        else:
            want = depth
            k = top if isinstance(top, int) else top.get(items[r["item_id"]]["question_type"],
                                                         top["default"])  # fmt: skip
            bad_len = len(r["retrieved"]) != want
            floor_may_shorten = pipeline == "config_4_rerank" and not r.get("rerank_fell_back")
        if bad_len or n > k or (n < k and not floor_may_shorten):
            out.append(r["item_id"])
    return out


def budget_for(route: dict | None, budgets: dict) -> tuple[str, dict | None]:
    """(intent, budget); `unrouted` when the router output did not parse;
    `unsupported` has no budget (declined)."""
    if route is None:
        return "unrouted", budgets["unrouted"]
    if route["intent"] == "unsupported":
        return "unsupported", None
    return route["intent"], budgets[route["intent"]]


def queries_for(question: str, route: dict | None, budget: dict) -> list[str]:
    """The question itself, or for a two-query budget the router's sub-queries
    (the question stands in for any missing one)."""
    if budget["sub_queries"] == 1:
        return [question]
    subs = [q for q in (route or {}).get("sub_queries", []) if isinstance(q, str) and q.strip()]
    return (subs + [question] * budget["sub_queries"])[: budget["sub_queries"]]


def post_for_query(fused: list[str], reranked: list[tuple[str, float]], seconds: float,
                   rerank_cfg: dict, top_n: int) -> tuple[list[str], bool]:  # fmt: skip
    """One query's post-rerank list and whether it fell back to RRF order (PRD 7.3)."""
    if seconds * 1000 > rerank_cfg["timeout_ms"]:
        return fused[:top_n], True
    return [c for c, _ in apply_floor(reranked, rerank_cfg["score_floor"])[:top_n]], False


def interleave(lists: list[list[str]], n: int) -> list[str]:
    """Round-robin over the per-query lists, first occurrence kept, up to n."""
    out: list[str] = []
    for i in range(max((len(x) for x in lists), default=0)):
        for x in lists:
            if i < len(x) and x[i] not in out:
                out.append(x[i])
    return out[:n]
