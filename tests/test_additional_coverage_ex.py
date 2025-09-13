import builtins
import csv
import io
import os
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

from rolling_returns.legacy.depot import _xirr_series
from rolling_returns.legacy.depotex import (
    read_csv_generic,
    rolling_mwr_xirr,
    rolling_time_weighted,
)

# Target imports
from rolling_returns.pipeline import apply_instrument_mapper, fifo_gains, read_fx, yearly_loss_pots


def test_read_fx_raises_on_missing_required_cols(tmp_path: Path):
    # Create FX CSV missing 'Currency' column
    p = tmp_path / "fx_bad.csv"
    p.write_text("Date,RateToBase\n2024-01-01,1.1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_fx(p, sep=",", dec=".")


def test_apply_instrument_mapper_requires_instrument_col(tmp_path: Path):
    # Mapper without 'Instrument' triggers ValueError
    mapper = tmp_path / "map_bad.csv"
    mapper.write_text("AssetType,Currency\nstock,EUR\n", encoding="utf-8")
    # Trades can be empty; the function validates mapper independently
    trades = pd.DataFrame(
        columns=[
            "Date",
            "Action",
            "Instrument",
            "Quantity",
            "Price",
            "Fees",
            "Tax",
            "Currency",
            "AssetType",
        ]
    )
    with pytest.raises(ValueError):
        apply_instrument_mapper(trades, mapper, sep=",", dec=".")


def test_fifo_gains_partial_lot_and_fees_fx(tmp_path: Path):
    # BUY 10 @ 100, BUY 5 @ 120, SELL 12 @ 130 with fees 1.0 should
    # consume 10 from lot1 and 2 from lot2
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "X",
                "Quantity": 10,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-01-10",
                "Action": "BUY",
                "Instrument": "X",
                "Quantity": 5,
                "Price": 120.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-01",
                "Action": "SELL",
                "Instrument": "X",
                "Quantity": 12,
                "Price": 130.0,
                "Fees": 1.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    fx = pd.DataFrame(columns=["Date", "Currency", "RateToBase"])  # empty → FX=1.0
    twg = fifo_gains(trades, fx, base_ccy="EUR")
    # Check realized gain: proceeds - cost_total
    # proceeds = 12 * 130 - 1 = 1559
    # cost_total = 10*100 + 2*120 = 1000 + 240 = 1240
    # realized = 319
    realized = float(
        twg.loc[(twg["Action"] == "SELL") & (twg["Instrument"] == "X"), "Realized_Gain_Base"].iloc[
            0
        ]
    )
    assert pytest.approx(realized, rel=1e-9) == 319.0


def test_yearly_loss_pots_with_soli_and_church_tax():
    # Two SELLs in the same year across different pots, with one loss to carry
    twg = pd.DataFrame(
        [
            {
                "Date": "2024-03-01",
                "Action": "SELL",
                "Instrument": "A",
                "AssetType": "stock",
                "Realized_Gain_Base": 1000.0,
            },
            {
                "Date": "2024-06-01",
                "Action": "SELL",
                "Instrument": "B",
                "AssetType": "fund",
                "Realized_Gain_Base": -300.0,
            },
            {
                "Date": "2024-09-01",
                "Action": "SELL",
                "Instrument": "C",
                "AssetType": "bond",
                "Realized_Gain_Base": 200.0,
            },
        ]
    )
    out = yearly_loss_pots(twg, fsa=100.0, base_rate=0.25, church_tax=0.08, soli=True)
    assert out.shape[0] == 1
    row = out.iloc[0]
    eff = 0.25 * 1.055 * (1 + 0.08)
    taxable_before = 1000.0 + 0.0 + 200.0  # fund loss (-300) carried against fund only
    fsa_used = 100.0
    taxable = taxable_before - fsa_used
    expected_tax = taxable * eff
    assert pytest.approx(row["Eff_Tax_Rate"], rel=1e-12) == eff
    assert pytest.approx(row["Tax_Paid"], rel=1e-9) == expected_tax


def test_legacy_read_csv_accepts_datum_and_renames_to_date(tmp_path: Path):
    # Create a minimal legacy CSV using 'Datum' instead of 'Date'
    p = tmp_path / "legacy.csv"
    p.write_text("Datum,End_NAV\n2024-01-01,100\n2024-01-02,101\n", encoding="utf-8")
    df = read_csv_generic(p, sep=",", dec=".")
    assert "Date" in df.columns
    assert pd.to_datetime(df.loc[0, "Date"]).year == 2024


def test_twr_series_flow_adjusted_requires_cash_flow():
    # Build df without Cash_Flow but ask for flow-adjusted → should raise
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "End_NAV": [100.0, 101.0, 102.0],
        }
    )
    with pytest.raises(ValueError):
        rolling_time_weighted(df, window=2, mode="flow-adjusted", business_days=True)


def test_depot_xirr_series_returns_nan_when_numpy_financial_missing(monkeypatch):
    # Force ImportError inside legacy.depot._xirr_series
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "numpy_financial":
            raise ImportError("forced for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "End_NAV": [100.0, 101.0, 102.0],
            "Cash_Flow": [0.0, 0.0, 0.0],
        }
    )
    out = _xirr_series(df, window=2, business_days=True)
    assert out.isna().all()


def test_depotex_rolling_mwr_xirr_raises_runtime_error_without_numpy_financial(monkeypatch):
    # Force ImportError inside legacy.depotex.rolling_mwr_xirr
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "numpy_financial":
            raise ImportError("forced for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "End_NAV": [100.0, 101.0, 102.0],
            "Cash_Flow": [0.0, 0.0, 0.0],
        }
    )
    with pytest.raises(RuntimeError):
        rolling_mwr_xirr(df, window=2, business_days=True, include_tax=False)
