"""PRD 7.4 structured answers: schema, CLI enforcement, contract checks. Inline data."""

from __future__ import annotations

import json

import pytest

from api.generate import claude_cli
from api.generate.claims import SCHEMA, SYSTEM_PROMPT, answer_text, contract_violations, render
from api.generate.generator import Answer
from scripts.eval_run import answer_fields

FIG = {"value": 7286, "unit": "millions", "currency": "USD", "period": "FY2024",
       "concept": "Inventories"}  # fmt: skip


def doc(claims, sufficient=True, reason=None):
    return {"answer_claims": claims, "sufficient_evidence": sufficient, "abstain_reason": reason}


def claim(cid="c1", text="Inventories were $7,286 million for fiscal 2024.", cites=("a",), fig=FIG):
    return {"claim_id": cid, "text": text, "citations": list(cites), "figure": fig}


def test_schema_and_prompt_carry_prd_7_4():
    assert SCHEMA["required"] == ["answer_claims", "sufficient_evidence", "abstain_reason"]
    item = SCHEMA["properties"]["answer_claims"]["items"]
    assert item["properties"]["citations"]["minItems"] == 1
    assert "Every claim MUST cite at least one chunk_id" in SYSTEM_PROMPT
    p = render("Q?", [("a", "text a"), ("b", "text b")])
    assert "[chunk_id: a]\ntext a" in p and p.endswith("Question: Q?")


def test_contract_violations_record_what_the_schema_cannot():
    assert contract_violations(doc([claim()]), ["a", "b"]) == []
    v = contract_violations(doc([claim(cites=("a", "z")), claim("c1", "Up 15% from 2023.",
                                                                fig=None)]), ["a"])  # fmt: skip
    assert v == ["duplicate claim_id", "c1: cites chunks not given ['z']",
                 "c1: number in text without a figure object"]  # fmt: skip
    assert contract_violations(doc([]), ["a"]) == ["sufficient_evidence true with no claims"]
    assert contract_violations(doc([], False, None), ["a"]) == [
        "insufficient evidence with no abstain_reason"
    ]
    assert answer_text(doc([], False, "no inventory figure")) == ""


def test_cli_passes_the_schema_and_requires_structured_output():
    cmd = claude_cli.build_command("p", "m", "s", SCHEMA)
    assert cmd[cmd.index("--json-schema") + 1] == json.dumps(SCHEMA)
    assert "--json-schema" not in claude_cli.build_command("p", "m", "s")
    out = {"result": "{}", "modelUsage": {"m": {}}, "usage": {"input_tokens": 1,
           "output_tokens": 1}, "structured_output": doc([claim()])}  # fmt: skip
    assert claude_cli.parse_output(json.dumps(out), structured=True).structured == doc([claim()])
    del out["structured_output"]
    with pytest.raises(claude_cli.CliError):
        claude_cli.parse_output(json.dumps(out), structured=True)
    assert claude_cli.parse_output(json.dumps(out)).structured is None


def test_answer_fields_keep_claims_and_the_models_abstention():
    a = Answer("t", "m", 1, 1, "claude_cli", structured=doc([claim()]))
    f = answer_fields(a, ["a"])
    assert f["verdict"] == "PASS" and f["answer"]["claims"][0]["figure"] == FIG
    assert f["contract_violations"] == []
    a = Answer("", "m", 1, 1, "claude_cli", structured=doc([], False, "no figure"))
    f = answer_fields(a, ["a"])
    assert f["answer"]["abstained"] and f["abstain_reason"] == "insufficient_evidence"
    assert answer_fields(Answer("t", "m", 1, 1), ["a"])["answer"]["claims"] == []
