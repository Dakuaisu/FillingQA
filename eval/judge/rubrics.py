"""Answer-correctness rubric and judge prompt (PRD 11.3). Explicit 1-5 anchors."""

from __future__ import annotations

RUBRIC = {
    5: "Correct and complete: every material fact in the reference is stated and none is "
       "contradicted; figures match the reference at its printed precision, for the right "
       "company and period.",
    4: "Correct in substance with a minor gap: the main fact is right, but a secondary detail "
       "is missing or a figure is rounded (within 0.5%) without changing the meaning.",
    3: "Partially correct: some required facts are right and others are missing or wrong "
       "(for example one of two compared values, or the right figure for the wrong period).",
    2: "Mostly incorrect: the main figure or claim is wrong, though related information from "
       "the filings is present.",
    1: "Incorrect or no answer: wrong, irrelevant, invented, or a refusal when the reference "
       "has an answer. For an item whose reference is null (the system should abstain), "
       "giving a specific answer scores 1 and declining scores 5.",
}  # fmt: skip

PROMPT = """You are grading an answer to a question about SEC filings against a reference answer.

Question:
<<QUESTION>>

Reference answer (null means the system should decline to answer):
<<REFERENCE>>

Answer to grade:
<<ANSWER>>

Score the answer from 1 to 5 using this rubric:
<<RUBRIC>>

Judge correctness against the reference only, not style or length. Return only a JSON object, \
with no other text: {"score": <1-5>, "rationale": "<one sentence>"}
"""


def render(question: str, reference: str | None, answer: str) -> str:
    rubric = "\n".join(f"{k}: {v}" for k, v in sorted(RUBRIC.items(), reverse=True))
    return (PROMPT.replace("<<QUESTION>>", question)
            .replace("<<REFERENCE>>", "null" if reference is None else reference)
            .replace("<<ANSWER>>", answer).replace("<<RUBRIC>>", rubric))  # fmt: skip
