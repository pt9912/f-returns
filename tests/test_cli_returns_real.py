from pathlib import Path

import pandas as pd

from rolling_returns.cli import main_rr


def test_cli_returns_real(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "C",
                "Quantity": 10,
                "Price": 100.0,
                "Fees": 1.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-15",
                "Action": "SELL",
                "Instrument": "C",
                "Quantity": -5,
                "Price": 110.0,
                "Fees": 1.0,
                "Tax": 0.5,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-04-10",
                "Action": "SELL",
                "Instrument": "C",
                "Quantity": -5,
                "Price": 120.0,
                "Fees": 1.0,
                "Tax": 1.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "C", "ClosePrice": 100.0},
            {"Date": "2024-02-15", "Instrument": "C", "ClosePrice": 110.0},
            {"Date": "2024-04-10", "Instrument": "C", "ClosePrice": 120.0},
        ]
    )
    tr = tmp_path / "tr.csv"
    pr = tmp_path / "pr.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--csv-in-sep",
            ",",
            "--csv-in-decimal",
            ".",
            "--output",
            str(out_dir / "res.csv"),
            "--output-prefix",
            str(out_dir),
            "--window",
            "30",
            "--business-days",
            "--annualize",
            "--money-weighted",
            "--plot",
            "--save-svg",
            "--fsa",
            "1000.0",
            "--tax-rate",
            "0.26375",
            "--church-tax",
            "0.0",
            "--soli",
            "--include-tax",
        ]
    )
    assert rc == 0
    assert (out_dir / "res.csv").exists()
