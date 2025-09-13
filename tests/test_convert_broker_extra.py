import argparse
import types
from pathlib import Path

import pandas as pd

from rolling_returns.converter.convert_broker import load_mapping
from rolling_returns.converter.convert_broker import main as conv_main
from rolling_returns.converter.generic import convert_prices_df, convert_trades_df


def test_load_mapping_none_returns_empty():
    assert load_mapping(None) == {}


def test_main_converts_both(tmp_path: Path):
    tr = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "action": "BUY",
                "symbol": "Z",
                "qty": 3,
                "price": 7.0,
                "fee": 0.1,
                "tax": 0.0,
                "currency": "EUR",
            }
        ]
    )
    pr = pd.DataFrame([{"date": "2024-01-02", "symbol": "Z", "close": 7.0}])
    tr_in = tmp_path / "tr.csv"
    pr_in = tmp_path / "pr.csv"
    tr.to_csv(tr_in, index=False)
    pr.to_csv(pr_in, index=False)

    map_tr = tmp_path / "map_tr.json"
    map_pr = tmp_path / "map_pr.json"
    map_tr.write_text(
        '{"date":"date","symbol":"symbol","action":"action","qty":"qty","price":"price","fee":"fee","tax":"tax","currency":"currency"}',
        encoding="utf-8",
    )
    map_pr.write_text('{"date":"date","symbol":"symbol","close":"close"}', encoding="utf-8")

    out_tr = tmp_path / "out_tr.csv"
    out_pr = tmp_path / "out_pr.csv"

    ns = argparse.Namespace(
        broker_trades=tr_in,
        broker_prices=pr_in,
        map_trades=map_tr,
        map_prices=map_pr,
        out_trades=out_tr,
        out_prices=out_pr,
        sep=",",
        decimal=".",
    )
    rc = conv_main(ns)
    assert rc == 0
    assert out_tr.exists() and out_pr.exists()
    # sanity
    dtr = pd.read_csv(out_tr)
    dpr = pd.read_csv(out_pr)
    assert {
        "Date",
        "Action",
        "Instrument",
        "Quantity",
        "Price",
        "Fees",
        "Tax",
        "Currency",
    }.issubset(set(dtr.columns))
    assert {"Date", "Instrument", "ClosePrice"}.issubset(set(dpr.columns))
