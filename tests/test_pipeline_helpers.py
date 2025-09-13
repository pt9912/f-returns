# tests/test_pipeline_helpers.py
from pathlib import Path

import pandas as pd
import pytest

from rolling_returns.pipeline import apply_instrument_mapper, read_fx, read_prices, read_trades


def test_read_trades_validation(tmp_path: Path):
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"Date": ["2024-01-01"]}).to_csv(bad, index=False)
    with pytest.raises(ValueError):
        read_trades(bad, ",", ".")


def test_read_prices_validation(tmp_path: Path):
    bad = tmp_path / "badp.csv"
    pd.DataFrame({"Date": ["2024-01-01"]}).to_csv(bad, index=False)
    with pytest.raises(ValueError):
        read_prices(bad, ",", ".")


def test_read_fx_missing_returns_empty(tmp_path: Path):
    assert read_fx(tmp_path / "missing.csv", ",", ".").empty


def test_apply_instrument_mapper(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "Action": "BUY",
                "Instrument": "AAA",
                "Quantity": 1,
                "Price": 1.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "AssetType": "stock",
                "Currency": "EUR",
            }
        ]
    )
    mp = tmp_path / "map.csv"
    pd.DataFrame(
        [
            {
                "Instrument": "AAA",
                "AssetType": "bond",
                "Currency": "USD",
                "Country": "US",
                "DividendWithholdingRate": 15.0,
            }
        ]
    ).to_csv(mp, index=False)
    apply_instrument_mapper(trades, mp, ",", ".")
    assert trades.loc[0, "AssetType"] == "bond"
    assert trades.loc[0, "Currency"] == "USD"
