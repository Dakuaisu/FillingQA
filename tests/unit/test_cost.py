"""cost_per_query (F-134). Inline data; prices as in eval/pricing.yaml's shape."""

from __future__ import annotations

import pytest

from eval.metrics.cost import DEV_NA, cost_per_query, tokens

PRICES = {"haiku": {"input": 1.0, "output": 5.0, "cache_write": 1.25, "cache_read": 0.1},
          "sonnet": {"input": 2.0, "output": 10.0, "cache_write": None,
                     "cache_read": 0.2}}  # fmt: skip


def u(i, o, cr=0, cc=0):
    return {"input_tokens": i, "output_tokens": o, "cache_read_tokens": cr,
            "cache_creation_tokens": cc}  # fmt: skip


def item(gen_model="haiku", gen=None, router=True):
    r = {"model_served": gen_model, "usage": gen if gen is not None else u(1000, 100)}
    if router:
        r["router"] = {"model_served": "haiku", "usage": u(500, 50)}
    return r


def test_router_and_generator_are_priced_and_averaged_over_items():
    # item 1: router 500*1 + 50*5 = 750; generator 1000*1 + 100*5 = 1500 -> 2250e-6
    # item 2: router 750; sonnet generator 1000*2 + 100*10 = 3000 -> 3750e-6
    c = cost_per_query([item(), item("sonnet")], PRICES, dev_backend=False)
    assert c == pytest.approx((2250 + 3750) / 2 / 1e6)
    assert tokens([item(), item("sonnet")])["input_tokens"] == 3000


def test_cache_tokens_priced_when_the_table_has_a_price():
    c = cost_per_query([item(gen=u(0, 0, cr=1_000_000, cc=1_000_000), router=False)], PRICES, False)
    assert c == pytest.approx(0.1 + 1.25)
    why = cost_per_query([item("sonnet", u(0, 0, cc=10), router=False)], PRICES, False)
    assert why == "pending: no cache_write price for sonnet"


def test_dev_backend_unpriced_models_and_missing_tokens_are_never_guessed():
    assert cost_per_query([item()], PRICES, dev_backend=True) == DEV_NA
    assert cost_per_query([item("opus")], PRICES, False) == "pending: no price for opus"
    r = item()
    r["router"]["usage"] = None
    assert cost_per_query([r], PRICES, False) == "pending: call tokens not recorded"
    declined = {"model_served": None, "usage": None, "router": {"model_served": "haiku",
                                                                "usage": u(500, 50)}}  # fmt: skip
    assert cost_per_query([declined], PRICES, False) == pytest.approx(750e-6)
