"""The answer-correctness judge (PRD 11.3). Calls the configured backend through
`api.generate.generator.complete`; every verdict is stamped with the judge's
backend, model served and family, and whether that family is the generator's
(PRD 11.3 asks for a different family; F-14)."""

from __future__ import annotations

import json
import re

from api.generate.generator import complete
from eval.judge.rubrics import render

FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)


class JudgeParseError(ValueError):
    """The judge's output is not the required JSON; recorded, never re-asked."""


def family(model_id: str) -> str:
    """The model family: the provider prefix of the model id ("claude", "gpt", ...)."""
    return model_id.split(",")[0].split("-", 1)[0].lower()


def parse(text: str) -> tuple[int, str]:
    m = FENCE.fullmatch(text.strip())
    s = m.group(1) if m else text.strip()
    try:
        doc = json.loads(s)
    except json.JSONDecodeError as e:
        raise JudgeParseError(f"not JSON: {e.msg}") from e
    if not isinstance(doc, dict) or set(doc) != {"score", "rationale"}:
        raise JudgeParseError("expected exactly score and rationale")
    if (
        not isinstance(doc["score"], int)
        or isinstance(doc["score"], bool)
        or not 1 <= doc["score"] <= 5
    ):
        raise JudgeParseError(f"score {doc['score']!r} not an integer 1-5")
    return doc["score"], str(doc["rationale"])


def judge(item: dict, answer: str, cfg: dict, tier: str, generator_model: str) -> dict:
    a = complete(render(item["question"], item["reference_answer"], answer), cfg, tier)
    score, rationale = parse(a.text)
    return {
        "item_id": item["item_id"], "score": score, "rationale": rationale,
        "judge_backend": a.backend, "judge_model": a.model, "judge_family": family(a.model),
        "generator_model": generator_model,
        "same_family_as_generator": family(a.model) == family(generator_model),
    }  # fmt: skip
