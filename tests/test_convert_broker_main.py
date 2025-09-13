import json
import types
from pathlib import Path

import pandas as pd

from rolling_returns.converter.convert_broker import main


class NS(types.SimpleNamespace):
    pass


def test_convert_broker_main_json(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "symbol": "X",
                "action": "BUY",
                "qty": 2,
                "price": 10.0,
                "fee": 0.5,
                "tax": 0.0,
                "currency": "EUR",
            }
        ]
    )
    prices = pd.DataFrame([{"date": "2024-01-02", "symbol": "X", "close": 10.0}])
    tr_in = tmp_path / "broker_trades.csv"
    pr_in = tmp_path / "broker_prices.csv"
    trades.to_csv(tr_in, index=False)
    prices.to_csv(pr_in, index=False)

    # IMPORTANT: convert_broker.main expects a *flat* mapping dict per file, not nested.
    trades_map = {
        "date": "date",
        "symbol": "symbol",
        "action": "action",
        "qty": "qty",
        "price": "price",
        "fee": "fee",
        "tax": "tax",
        "currency": "currency",
    }
    prices_map = {"date": "date", "symbol": "symbol", "close": "close"}

    map_tr = tmp_path / "map_trades.json"
    map_pr = tmp_path / "map_prices.json"
    map_tr.write_text(json.dumps(trades_map), encoding="utf-8")
    map_pr.write_text(json.dumps(prices_map), encoding="utf-8")

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    ns = NS(
        broker_trades=tr_in,
        broker_prices=pr_in,
        map_trades=map_tr,
        map_prices=map_pr,
        out_trades=out_dir / "trades_std.csv",
        out_prices=out_dir / "prices_std.csv",
        sep=",",
        decimal=".",
    )
    rc = main(ns)
    assert rc == 0
    assert (out_dir / "trades_std.csv").exists()
    assert (out_dir / "prices_std.csv").exists()
