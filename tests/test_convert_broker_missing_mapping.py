import types
from pathlib import Path

import pandas as pd

from rolling_returns.converter.convert_broker import main


class NS(types.SimpleNamespace):
    pass


def test_convert_broker_no_mapping_uses_defaults(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "Y",
                "Quantity": 1,
                "Price": 5.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            }
        ]
    )
    prices = pd.DataFrame([{"Date": "2024-01-02", "Instrument": "Y", "ClosePrice": 5.0}])
    tr_in = tmp_path / "btr.csv"
    pr_in = tmp_path / "bpr.csv"
    trades.to_csv(tr_in, index=False)
    prices.to_csv(pr_in, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    ns = NS(
        broker_trades=tr_in,
        broker_prices=pr_in,
        map_trades=None,
        map_prices=None,
        out_trades=out_dir / "trades_std.csv",
        out_prices=out_dir / "prices_std.csv",
        sep=",",
        decimal=".",
    )
    rc = main(ns)
    assert rc == 0
    assert (out_dir / "trades_std.csv").exists()
    assert (out_dir / "prices_std.csv").exists()
