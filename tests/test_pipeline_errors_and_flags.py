from pathlib import Path

import pandas as pd
import pytest

from rolling_returns.pipeline import run_pipeline


def test_pipeline_missing_trades_raises(tmp_path: Path):
    prices = pd.DataFrame([{"Date": "2024-01-02", "Instrument": "Z", "ClosePrice": 10.0}])
    pr_in = tmp_path / "prices.csv"
    prices.to_csv(pr_in, index=False)
    with pytest.raises(ValueError):
        run_pipeline(
            trades_file=None,
            prices_file=pr_in,
            nav_file=None,
            instrument_mapper=None,
            fx_file=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            base_currency="EUR",
            window=30,
            business_days=False,
            annualize=False,
            money_weighted=False,
            plot=False,
            save_svg=False,
            fsa=1000.0,
            tax_rate=0.25,
            church_tax=0.0,
            soli=False,
            include_tax=False,
            output=None,
            output_prefix=tmp_path,
        )


def test_pipeline_prices_missing_column_raises(tmp_path: Path):
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
            }
        ]
    )
    prices = pd.DataFrame([{"Date": "2024-01-02", "Instrument": "Z", "Close": 10.0}])  # wrong col
    tr_in = tmp_path / "tr.csv"
    pr_in = tmp_path / "pr.csv"
    trades.to_csv(tr_in, index=False)
    prices.to_csv(pr_in, index=False)
    with pytest.raises(ValueError):
        run_pipeline(
            trades_file=tr_in,
            prices_file=pr_in,
            nav_file=None,
            instrument_mapper=None,
            fx_file=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            base_currency="EUR",
            window=30,
            business_days=False,
            annualize=False,
            money_weighted=False,
            plot=False,
            save_svg=False,
            fsa=1000.0,
            tax_rate=0.25,
            church_tax=0.0,
            soli=False,
            include_tax=False,
            output=None,
            output_prefix=tmp_path,
        )


def test_pipeline_plot_include_tax_false_no_mwr(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "Z",
                "Quantity": 2,
                "Price": 10.0,
                "Fees": 0.1,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-02",
                "Action": "SELL",
                "Instrument": "Z",
                "Quantity": -1,
                "Price": 11.0,
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
            {"Date": "2024-02-02", "Instrument": "Z", "ClosePrice": 11.0},
        ]
    )
    tr_in = tmp_path / "tr.csv"
    pr_in = tmp_path / "pr.csv"
    trades.to_csv(tr_in, index=False)
    prices.to_csv(pr_in, index=False)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    res = run_pipeline(
        trades_file=tr_in,
        prices_file=pr_in,
        nav_file=None,
        instrument_mapper=None,
        fx_file=None,
        csv_in_sep=",",
        csv_in_decimal=".",
        base_currency="EUR",
        window=20,
        business_days=False,
        annualize=False,
        money_weighted=False,  # ensure MWR curve omitted branch
        plot=True,
        save_svg=False,
        fsa=1000.0,
        tax_rate=0.25,
        church_tax=0.0,
        soli=False,
        include_tax=False,  # branch without tax incorporation
        output=None,
        output_prefix=out_dir,
    )
    assert res["returns"] is not None
    # file likely named 'returns.png' per earlier test
    assert (out_dir / "returns.png").exists() or (out_dir / "returns.svg").exists()
