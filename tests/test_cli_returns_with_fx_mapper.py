from pathlib import Path

import pandas as pd

from rolling_returns.cli import main_rr


def test_cli_returns_with_fx_and_mapper(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "U",
                "Quantity": 10,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "USD",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-01",
                "Action": "SELL",
                "Instrument": "U",
                "Quantity": -5,
                "Price": 110.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "USD",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "U", "ClosePrice": 100.0},
            {"Date": "2024-02-01", "Instrument": "U", "ClosePrice": 110.0},
        ]
    )
    # Pipeline.read_fx expects: Date, Currency, RateToBase (for base currency)
    fx = pd.DataFrame(
        [
            {"Date": "2024-01-01", "Currency": "USD", "RateToBase": 0.9},
            {"Date": "2024-02-01", "Currency": "USD", "RateToBase": 0.92},
        ]
    )
    mapper = pd.DataFrame(
        [
            {
                "Instrument": "U",
                "AssetType": "stock",
                "Currency": "USD",
                "Country": "US",
                "DividendWithholdingRate": 15.0,
            }
        ]
    )
    tr = tmp_path / "tr.csv"
    pr = tmp_path / "pr.csv"
    fxp = tmp_path / "fx.csv"
    mp = tmp_path / "map.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)
    fx.to_csv(fxp, index=False)
    mapper.to_csv(mp, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--fx-file",
            str(fxp),
            "--instrument-mapper",
            str(mp),
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
            "--annualize",
            "--money-weighted",
        ]
    )
    assert rc == 0
    assert (out_dir / "res.csv").exists()
