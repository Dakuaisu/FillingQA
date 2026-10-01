"""Phase 2 naive baseline, end to end: question in, answer out.

python -m api.query.baseline "What were Apple's total net sales in fiscal 2025?"
python -m api.query.baseline --retrieve-only "..."
"""

from __future__ import annotations

import argparse

from api.config import baseline, generation
from api.db import connect
from api.generate.generator import generate
from api.index.embed import load_model
from api.query.retrieve import dense_top_k, embed_question


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2 naive baseline.")
    parser.add_argument("question")
    parser.add_argument("--retrieve-only", action="store_true", help="skip generation")
    args = parser.parse_args()

    model, emb = load_model()
    with connect() as conn:
        chunks, plan = dense_top_k(
            conn, embed_question(model, emb, args.question), baseline()["top_k"]
        )
    print(f"question: {args.question}")
    print(f"plan: {plan}")
    for c in chunks:
        print(f"  {c.distance:.4f}  {c.chunk_id}  {c.text.splitlines()[0]}")
    if args.retrieve_only:
        return
    answer = generate(args.question, chunks, generation(), "tier_small")
    print(f"model: {answer.model}")
    print(f"usage: input_tokens={answer.input_tokens} output_tokens={answer.output_tokens}")
    print("answer:")
    print(answer.text)


if __name__ == "__main__":
    main()
