from pathlib import Path

import pandas as pd

from rolling_returns.pipeline import run_pipeline


def test_pipeline_navfile_branch_with_plot(tmp_path: Path):
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
    nav = pd.DataFrame(
        [
            {"Date": "2024-01-02", "End_NAV": 100.0},
            {"Date": "2024-02-01", "End_NAV": 101.0},
            {"Date": "2024-03-15", "End_NAV": 100.5},
        ]
    )
    tr_in = tmp_path / "tr.csv"
    pr_in = tmp_path / "pr.csv"
    nav_in = tmp_path / "nav.csv"
    trades.to_csv(tr_in, index=False)
    prices.to_csv(pr_in, index=False)
    nav.to_csv(nav_in, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    res = run_pipeline(
        trades_file=tr_in,
        prices_file=pr_in,
        nav_file=nav_in,  # forces nav-file branch
        instrument_mapper=None,
        fx_file=None,
        csv_in_sep=",",
        csv_in_decimal=".",
        base_currency="EUR",
        window=60,
        business_days=False,
        annualize=True,
        money_weighted=True,
        plot=True,
        save_svg=True,
        fsa=1000.0,
        tax_rate=0.25,
        church_tax=0.0,
        soli=False,
        include_tax=True,
        output=None,
        output_prefix=out_dir,
    )
    # plotting should have produced files
    ret = res["returns"]
    assert ret is not None
    svg = out_dir / "returns.svg"
    png = out_dir / "returns.png"  # if code uses this name; fallback check on svg
    assert svg.exists() or png.exists()
