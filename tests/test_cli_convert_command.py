import json
from pathlib import Path

import pandas as pd

from rolling_returns.cli import main_rr


def test_cli_convert(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "symbol": "Z",
                "action": "BUY",
                "qty": 3,
                "price": 7.0,
                "fee": 0.1,
                "tax": 0.0,
                "currency": "EUR",
            }
        ]
    )
    prices = pd.DataFrame([{"date": "2024-01-02", "symbol": "Z", "close": 7.0}])
    tr_in = tmp_path / "tr_in.csv"
    pr_in = tmp_path / "pr_in.csv"
    trades.to_csv(tr_in, index=False)
    prices.to_csv(pr_in, index=False)

    map_tr = tmp_path / "map_tr.json"
    map_pr = tmp_path / "map_pr.json"
    map_tr.write_text(
        json.dumps(
            {
                "date": "date",
                "symbol": "symbol",
                "action": "action",
                "qty": "qty",
                "price": "price",
                "fee": "fee",
                "tax": "tax",
                "currency": "currency",
            }
        ),
        encoding="utf-8",
    )
    map_pr.write_text(
        json.dumps({"date": "date", "symbol": "symbol", "close": "close"}), encoding="utf-8"
    )

    out_tr = tmp_path / "tr_out.csv"
    out_pr = tmp_path / "pr_out.csv"

    rc = main_rr(
        [
            "convert",
            "generic",  # required subcommand
            "--broker-trades",
            str(tr_in),
            "--broker-prices",
            str(pr_in),
            "--map-trades",
            str(map_tr),
            "--map-prices",
            str(map_pr),
            "--out-trades",
            str(out_tr),
            "--out-prices",
            str(out_pr),
            "--sep",
            ",",
            "--decimal",
            ".",
        ]
    )
    assert rc == 0
    assert out_tr.exists()
    assert out_pr.exists()
