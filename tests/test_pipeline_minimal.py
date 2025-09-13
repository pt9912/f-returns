import os
from pathlib import Path

import pandas as pd

from rolling_returns.pipeline import run_pipeline


def test_run_pipeline_minimal(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "AAA",
                "Quantity": 10,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
            },
            {
                "Date": "2024-03-05",
                "Action": "SELL",
                "Instrument": "AAA",
                "Quantity": -5,
                "Price": 110.0,
                "Fees": 0.0,
                "Tax": 0.0,
            },
            {
                "Date": "2024-06-10",
                "Action": "SELL",
                "Instrument": "AAA",
                "Quantity": -5,
                "Price": 120.0,
                "Fees": 0.0,
                "Tax": 0.0,
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "AAA", "ClosePrice": 100.0},
            {"Date": "2024-03-05", "Instrument": "AAA", "ClosePrice": 110.0},
            {"Date": "2024-06-10", "Instrument": "AAA", "ClosePrice": 120.0},
        ]
    )
    trades_file = tmp_path / "trades.csv"
    prices_file = tmp_path / "prices.csv"
    trades.to_csv(trades_file, index=False)
    prices.to_csv(prices_file, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    res = run_pipeline(
        trades_file=trades_file,
        prices_file=prices_file,
        nav_file=None,
        instrument_mapper=None,
        fx_file=None,
        csv_in_sep=",",
        csv_in_decimal=".",
        base_currency="EUR",
        window=30,
        business_days=True,
        annualize=True,
        output=None,
        output_prefix=out_dir,
    )
    assert isinstance(res, dict)
    assert (out_dir / "nav.csv").exists()
