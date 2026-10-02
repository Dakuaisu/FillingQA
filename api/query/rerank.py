"""Cross-encoder reranking (PRD 7.3) over the fused pre-rerank list.

Scores are the cross-encoder's logit through a sigmoid, so the score floor is on
a 0-1 scale ("~0.3 normalized"). The floor is uncalibrated until reviewed items
exist (`rerank.floor_calibration: pending`).
"""

from __future__ import annotations

import math
import time


def resolve_device(device: str) -> str:
    """`auto`: mps, else cuda, else cpu (F-137). Any other value is used as given."""
    if device != "auto":
        return device
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_reranker(cfg: dict):
    from sentence_transformers import CrossEncoder  # torch is heavy; load on use

    return CrossEncoder(
        cfg["model"], revision=cfg["revision"], device=resolve_device(cfg["device"])
    )


def machine() -> dict:
    """What a latency number depends on: device, torch, CPU, GPU, RAM."""
    import platform
    import subprocess

    import torch

    def sysctl(name: str) -> str:
        r = subprocess.run(["sysctl", "-n", name], capture_output=True, text=True, check=False)
        return r.stdout.strip()

    gpu = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True,
                         text=True, check=False).stdout  # fmt: skip
    chip = next(
        (ln.split(":", 1)[1].strip() for ln in gpu.splitlines() if "Chipset Model" in ln), ""
    )
    cores = next((ln.split(":", 1)[1].strip() for ln in gpu.splitlines()
                  if "Total Number of Cores" in ln), "")  # fmt: skip
    mem = sysctl("hw.memsize")
    return {
        "torch": torch.__version__, "platform": platform.platform(),
        "cpu": sysctl("machdep.cpu.brand_string") or platform.processor(),
        "gpu": f"{chip} ({cores} GPU cores)" if chip else "",
        "ram_gb": round(int(mem) / 2**30, 1) if mem.isdigit() else None,
        "mps_available": torch.backends.mps.is_available(),
    }  # fmt: skip


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def order(ids: list[str], scores: list[float]) -> list[tuple[str, float]]:
    """(chunk_id, score), score descending, ties to the smaller chunk id."""
    return sorted(zip(ids, scores, strict=True), key=lambda x: (-x[1], x[0]))


def apply_floor(ranked: list[tuple[str, float]], floor: float) -> list[tuple[str, float]]:
    """Drop chunks scoring below the floor; an empty result means abstain (PRD 7.3)."""
    return [(c, s) for c, s in ranked if s >= floor]


def top_n_for(question_type: str, cfg: dict) -> int:
    return cfg["top_n_synthesis"] if question_type == "synthesis" else cfg["top_n"]


def rerank(
    model, question: str, chunks: list[tuple[str, str]]
) -> tuple[list[tuple[str, float]], float]:
    """All candidates in one forward pass (PRD 7.3). Returns (ranked, seconds)."""
    t0 = time.monotonic()
    logits = model.predict(
        [(question, text) for _, text in chunks],
        batch_size=len(chunks) or 1,
        activation_fn=lambda x: x,
        convert_to_numpy=True,
    )
    scores = [sigmoid(float(x)) for x in logits]
    return order([c for c, _ in chunks], scores), time.monotonic() - t0
