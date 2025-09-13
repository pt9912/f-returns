from pathlib import Path

import pytest

from rolling_returns.pipeline import run_pipeline


def test_pipeline_ignores_missing_optional_files(tmp_path: Path):
    # Provide a non-existing optional mapper and fx file; run should still succeed
    dummy_trades = tmp_path / "tr.csv"
    dummy_prices = tmp_path / "pr.csv"
    dummy_prices.write_text("Date,Instrument,ClosePrice\n2024-01-01,AAA,10.0\n", encoding="utf-8")

    dummy_trades.write_text(
        "Date,Action,Instrument,Quantity,Price,Fees,Tax,Currency\n2024-01-01,BUY,AAA,1,10.0,0.0,0.0,EUR\n",
        encoding="utf-8",
    )
    rc = run_pipeline(
        trades_file=dummy_trades,
        prices_file=dummy_prices,
        nav_file=None,
        instrument_mapper=tmp_path / "missing_mapper.csv",
        fx_file=tmp_path / "missing_fx.csv",
        base_currency="EUR",
        csv_in_sep=",",
        csv_in_decimal=".",
        window=10,
        business_days=True,
        annualize=False,
        output_prefix=tmp_path,
    )
    assert isinstance(rc, dict)
