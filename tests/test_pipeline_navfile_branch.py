from pathlib import Path

import pandas as pd

from rolling_returns.pipeline import run_pipeline


def test_pipeline_with_navfile(tmp_path: Path):
    # Prepare trades minimal (still required by pipeline for returns computation)
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "Z",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    nav = pd.DataFrame(
        [
            {"Date": "2024-01-02", "End_NAV": 100.0},
            {"Date": "2024-02-01", "End_NAV": 101.0},
            {"Date": "2024-03-01", "End_NAV": 102.5},
        ]
    )
    tr = tmp_path / "tr.csv"
    nv = tmp_path / "nav.csv"
    trades.to_csv(tr, index=False)
    nav.to_csv(nv, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    res = run_pipeline(
        trades_file=tr,
        prices_file=None,
        nav_file=nv,
        instrument_mapper=None,
        fx_file=None,
        csv_in_sep=",",
        csv_in_decimal=".",
        base_currency="EUR",
        window=30,
        business_days=False,
        annualize=True,
        output=out_dir / "res.csv",
        output_prefix=out_dir,
        # include_tax True exercises branch; tax values are 0, fine
    )
    assert (out_dir / "res.csv").exists()
