from pathlib import Path

import pandas as pd

from rolling_returns.pipeline import run_pipeline


def test_pipeline_full_branch(tmp_path: Path):
    # trades, prices, fx to cover multiple branches
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "Z",
                "Quantity": 3,
                "Price": 10.0,
                "Fees": 0.1,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-01",
                "Action": "DIVIDEND",
                "Instrument": "Z",
                "Quantity": 0,
                "Price": 1.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-03-15",
                "Action": "SELL",
                "Instrument": "Z",
                "Quantity": -1,
                "Price": 12.0,
                "Fees": 0.1,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "Z", "ClosePrice": 10.0},
            {"Date": "2024-02-01", "Instrument": "Z", "ClosePrice": 10.5},
            {"Date": "2024-03-15", "Instrument": "Z", "ClosePrice": 11.5},
        ]
    )
    fx = pd.DataFrame([{"Date": "2024-01-02", "Currency": "EUR", "RateToBase": 1.0}])

    tr_in = tmp_path / "tr.csv"
    pr_in = tmp_path / "pr.csv"
    fx_in = tmp_path / "fx.csv"
    trades.to_csv(tr_in, index=False)
    prices.to_csv(pr_in, index=False)
    fx.to_csv(fx_in, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    res = run_pipeline(
        trades_file=tr_in,
        prices_file=pr_in,
        nav_file=None,
        instrument_mapper=None,
        fx_file=fx_in,
        csv_in_sep=",",
        csv_in_decimal=".",
        base_currency="EUR",
        window=60,
        business_days=True,
        annualize=True,
        money_weighted=True,
        plot=False,
        save_svg=False,
        fsa=1000.0,
        tax_rate=0.25,
        church_tax=0.0,
        soli=False,
        include_tax=True,
        output=None,
        output_prefix=out_dir,
    )
    # Should create outputs and return dict with keys
    assert res["nav"] is not None and res["returns"] is not None
    assert (out_dir / "nav.csv").exists()
