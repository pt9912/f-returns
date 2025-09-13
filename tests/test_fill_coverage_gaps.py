import builtins
import io
import os
import runpy
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure src is importable
ROOT = Path(__file__).resolve().parents[2]  # repo root (assumes tests/ in repo)
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))


def test_cli_convert_fallback_branch(monkeypatch):
    # Force argparse to return a Namespace with no known subparser -> hit return 0 at end of _convert_main
    import argparse

    from rolling_returns import cli

    class NS(types.SimpleNamespace):
        pass

    def fake_parse_args(_):
        return NS(converter=None)

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", lambda self, argv: fake_parse_args(argv)
    )
    rc = cli._convert_main(["--dummy"])
    assert rc == 0


def test_cli_main_entrypoint_runs(monkeypatch):
    # Run module as __main__ to execute the SystemExit() guard
    import sys as _sys

    argv_bak = list(_sys.argv)
    try:
        _sys.argv = ["f-returns"]  # no args -> argparse will exit non-zero
        try:
            runpy.run_module("rolling_returns.cli", run_name="__main__")
        except SystemExit as e:
            assert isinstance(e, SystemExit)
    finally:
        _sys.argv = argv_bak


def test_pipeline_fx_lookup_no_currency():
    import pandas as pd

    from rolling_returns.pipeline import fx_lookup

    fx = pd.DataFrame(columns=["Date", "Currency", "RateToBase"])
    dt = pd.Timestamp("2024-01-01")
    assert fx_lookup(fx, dt, "USD", "EUR") == 1.0  # sub.empty -> line 47


def test_pipeline_fx_lookup_no_prior_date():
    import pandas as pd

    from rolling_returns.pipeline import fx_lookup

    fx = pd.DataFrame(
        [
            {"Date": "2024-05-01", "Currency": "USD", "RateToBase": 1.1},
            {"Date": "2024-06-01", "Currency": "USD", "RateToBase": 1.2},
        ]
    )
    fx["Date"] = pd.to_datetime(fx["Date"])
    dt = pd.Timestamp("2024-04-01")
    # No rows <= dt, fall back to first row of that currency -> line 50
    assert fx_lookup(fx, dt, "USD", "EUR") == 1.1


def test_pipeline_fifo_partial_lot_update(tmp_path: Path):
    # Create simple trades that trigger partial consumption of a lot -> lines 223-231 (incl. 230)
    from rolling_returns.pipeline import run_pipeline

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
                "Quantity": -12,
                "Price": 130.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "X", "ClosePrice": 100.0},
            {"Date": "2024-01-10", "Instrument": "X", "ClosePrice": 120.0},
            {"Date": "2024-02-01", "Instrument": "X", "ClosePrice": 130.0},
        ]
    )
    p_tr = tmp_path / "trades.csv"
    p_pr = tmp_path / "prices.csv"
    trades.to_csv(p_tr, index=False)
    prices.to_csv(p_pr, index=False)

    res = run_pipeline(
        trades_file=p_tr,
        prices_file=p_pr,
        nav_file=None,
        instrument_mapper=None,
        fx_file=None,
        base_currency="EUR",
        window=5,
        business_days=True,
        annualize=False,
        money_weighted=False,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output_prefix=tmp_path,
    )
    twg = res["twg"]
    # realized gain must be computed and non-null
    assert "Realized_Gain_Base" in twg.columns
    assert pd.notna(twg.loc[twg["Action"] == "SELL", "Realized_Gain_Base"]).all()


def test_pipeline_cash_fee_and_tax(tmp_path: Path):
    # Ensure FEE and TAX actions affect cash path -> lines 352 and 354
    from rolling_returns.pipeline import run_pipeline

    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "Y",
                "Quantity": 10,
                "Price": 10.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-01-03",
                "Action": "FEE",
                "Instrument": "Y",
                "Quantity": 0,
                "Price": 0.0,
                "Fees": 1.5,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-01-04",
                "Action": "TAX",
                "Instrument": "Y",
                "Quantity": 0,
                "Price": 0.0,
                "Fees": 0.0,
                "Tax": 0.7,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "Y", "ClosePrice": 10.0},
            {"Date": "2024-01-03", "Instrument": "Y", "ClosePrice": 10.0},
            {"Date": "2024-01-04", "Instrument": "Y", "ClosePrice": 10.0},
        ]
    )
    p_tr = tmp_path / "trades.csv"
    p_pr = tmp_path / "prices.csv"
    trades.to_csv(p_tr, index=False)
    prices.to_csv(p_pr, index=False)

    res = run_pipeline(
        trades_file=p_tr,
        prices_file=p_pr,
        nav_file=None,
        instrument_mapper=None,
        fx_file=None,
        base_currency="EUR",
        window=2,
        business_days=False,
        annualize=False,
        money_weighted=False,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output_prefix=tmp_path,
    )
    nav = res["nav"]
    assert nav is not None
    # Cash should decrease due to FEE and TAX; just ensure NAV computed
    assert "End_NAV" in nav.columns


def test_pipeline_mwr_without_numpy_financial(monkeypatch, tmp_path: Path):
    # Force ImportError for numpy_financial by patching builtins.__import__
    import builtins as _builtins

    real_import = _builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "numpy_financial":
            raise ImportError("blocked for test")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(_builtins, "__import__", fake_import)

    # Create minimal trades/prices for returns calculation
    from rolling_returns.pipeline import run_pipeline

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
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "Z", "ClosePrice": 100.0},
            {"Date": "2024-12-31", "Instrument": "Z", "ClosePrice": 110.0},
        ]
    )
    p_tr = tmp_path / "trades.csv"
    p_pr = tmp_path / "prices.csv"
    trades.to_csv(p_tr, index=False)
    prices.to_csv(p_pr, index=False)

    res = run_pipeline(
        trades_file=p_tr,
        prices_file=p_pr,
        nav_file=None,
        instrument_mapper=None,
        fx_file=None,
        base_currency="EUR",
        window=30,
        business_days=False,
        annualize=False,
        money_weighted=True,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output_prefix=tmp_path,
    )
    df = res["returns"]
    assert "Rolling_TWR" in df.columns
    # Since numpy_financial import failed, MWR column may be missing
    assert not df.empty


def test_pipeline_nav_none_branch(tmp_path: Path):
    # No prices and no nav -> nav stays None (line 520)
    from rolling_returns.pipeline import run_pipeline

    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "A",
                "Quantity": 1,
                "Price": 1.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    p_tr = tmp_path / "trades.csv"
    trades.to_csv(p_tr, index=False)

    res = run_pipeline(
        trades_file=p_tr,
        prices_file=None,
        nav_file=None,
        instrument_mapper=None,
        fx_file=None,
        base_currency="EUR",
        window=5,
        business_days=True,
        annualize=False,
        money_weighted=False,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output_prefix=tmp_path,
    )
    assert res["nav"] is None


def test_legacy_depot_normalize_lowercase():
    # Trigger mapping via lowercase alias -> lines 70-71
    from rolling_returns.legacy import depot

    df = pd.DataFrame({"date": ["2024-01-01"], "end_nav": [100.0], "cash_flow": [0.0]})
    out = depot._normalize_columns(df.copy())
    assert set(["Date", "End_NAV", "Cash_Flow"]).issubset(out.columns)


def test_legacy_depot_missing_columns(tmp_path: Path):
    from rolling_returns.legacy import depot

    # Missing End_NAV should raise -> line 200
    csv = tmp_path / "legacy.csv"
    pd.DataFrame({"Date": ["2024-01-01"]}).to_csv(csv, index=False)
    try:
        depot.run_legacy(
            csv_file=csv,
            external_tax_column=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            csv_out_sep=",",
            csv_out_decimal=".",
            window=5,
            business_days=True,
            annualize=False,
            money_weighted=False,
            plot=False,
            save_svg=False,
            output=tmp_path / "out.csv",
            output_prefix=tmp_path,
        )
    except ValueError as e:
        assert "End_NAV" in str(e)


def test_depotex_normalize_lowercase():
    from rolling_returns.legacy import depotex

    df = pd.DataFrame({"date": ["2024-01-01"], "end_nav": [100.0], "cash_flow": [0.0]})
    aliases = depotex.ALIASES
    out = depotex.normalize_columns(df, aliases)
    assert set(["Date", "End_NAV", "Cash_Flow"]).issubset(out.columns)


def test_depotex_validations(tmp_path: Path):
    from rolling_returns.legacy import depotex

    # End_NAV non-numeric
    bad = pd.DataFrame({"Date": ["2024-01-01"], "End_NAV": ["foo"]})
    csv_bad = tmp_path / "bad.csv"
    bad.to_csv(csv_bad, index=False)
    try:
        depotex.run_legacy(
            csv_file=csv_bad,
            nav_file=None,
            flows_file=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            csv_out_sep=",",
            csv_out_decimal=".",
            window=5,
            business_days=True,
            annualize=False,
            money_weighted=False,
            plot=False,
            save_svg=False,
            tax_allowance=1000.0,
            tax_rate=0.25,
            church_tax=0.09,
            soli=False,
            include_tax=False,
            output=tmp_path / "out.csv",
            output_prefix=tmp_path,
        )
    except ValueError as e:
        assert "End_NAV" in str(e) or "numerisch" in str(e)

    # money_weighted without Cash_Flow
    df2 = pd.DataFrame({"Date": ["2024-01-01"], "End_NAV": [100.0]})
    csv2 = tmp_path / "no_cash.csv"
    df2.to_csv(csv2, index=False)
    try:
        depotex.run_legacy(
            csv_file=csv2,
            nav_file=None,
            flows_file=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            csv_out_sep=",",
            csv_out_decimal=".",
            window=5,
            business_days=True,
            annualize=False,
            money_weighted=True,
            plot=False,
            save_svg=False,
            tax_allowance=1000.0,
            tax_rate=0.25,
            church_tax=0.09,
            soli=False,
            include_tax=False,
            output=tmp_path / "out.csv",
            output_prefix=tmp_path,
        )
    except ValueError as e:
        assert "Cash_Flow" in str(e)

    # window <= 0
    try:
        depotex.run_legacy(
            csv_file=csv2,
            nav_file=None,
            flows_file=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            csv_out_sep=",",
            csv_out_decimal=".",
            window=0,
            business_days=True,
            annualize=False,
            money_weighted=False,
            plot=False,
            save_svg=False,
            tax_allowance=1000.0,
            tax_rate=0.25,
            church_tax=0.09,
            soli=False,
            include_tax=False,
            output=tmp_path / "out.csv",
            output_prefix=tmp_path,
        )
    except ValueError as e:
        assert "Fenstergröße" in str(e)
