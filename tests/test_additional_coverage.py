import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_cli_version_subcommand_runs():
    code, out, err = _run([sys.executable, "-m", "rolling_returns.cli", "version"])
    assert code == 0
    assert "version" in out.lower() or "unknown" in out.lower()


def test_cli_returns_minimal(tmp_path: Path):
    # Minimal trades + prices with required 'ClosePrice' header
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
            {"Date": "2024-01-02", "Instrument": "X", "ClosePrice": 100.0, "Currency": "EUR"},
            {"Date": "2024-01-10", "Instrument": "X", "ClosePrice": 120.0, "Currency": "EUR"},
            {"Date": "2024-02-01", "Instrument": "X", "ClosePrice": 130.0, "Currency": "EUR"},
        ]
    )
    tr = tmp_path / "trades.csv"
    pr = tmp_path / "prices.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)

    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"


def test_cli_returns_fx_path(tmp_path: Path):
    # Trades in USD + prices in USD, using required 'ClosePrice' header
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "Y",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "USD",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "Y", "ClosePrice": 100.0, "Currency": "USD"},
        ]
    )
    tr = tmp_path / "trades.csv"
    pr = tmp_path / "prices.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)

    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"


def test_depotex_basic_aggregate(tmp_path: Path):
    from rolling_returns.legacy import depotex

    df = pd.DataFrame(
        [
            {"Date": "2024-01-06", "NAV": 100.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-07", "NAV": 101.0, "Cash_Flow": 1.0},
        ]
    )
    out = depotex.aggregate_by_date(df)
    # Minimal sanity checks (columns observed in your build: Date & Cash_Flow)
    assert "Date" in out.columns
    assert "Cash_Flow" in out.columns


def test_cli_convert_generic_smoke(tmp_path: Path):
    broker_trades = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "symbol": "Z",
                "action": "BUY",
                "qty": 3,
                "price": 7.0,
                "fee": 0.1,
                "tax": 0.0,
                "currency": "EUR",
            }
        ]
    )
    broker_prices = pd.DataFrame([{"date": "2024-01-02", "symbol": "Z", "close": 7.0}])
    bt = tmp_path / "broker_trades.csv"
    bp = tmp_path / "broker_prices.csv"
    broker_trades.to_csv(bt, index=False)
    broker_prices.to_csv(bp, index=False)

    map_tr = tmp_path / "map_tr.json"
    map_pr = tmp_path / "map_pr.json"
    map_tr.write_text(
        json.dumps(
            {
                "date": "date",
                "symbol": "symbol",
                "action": "action",
                "qty": "qty",
                "price": "price",
                "fee": "fee",
                "tax": "tax",
                "currency": "currency",
            }
        ),
        encoding="utf-8",
    )
    map_pr.write_text(
        json.dumps({"date": "date", "symbol": "symbol", "close": "close"}), encoding="utf-8"
    )

    out_tr = tmp_path / "trades.csv"
    out_pr = tmp_path / "prices.csv"
    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "convert",
            "generic",
            "--broker-trades",
            str(bt),
            "--broker-prices",
            str(bp),
            "--map-trades",
            str(map_tr),
            "--map-prices",
            str(map_pr),
            "--out-trades",
            str(out_tr),
            "--out-prices",
            str(out_pr),
            "--sep",
            ",",
            "--decimal",
            ".",
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"
    assert out_tr.exists() and out_pr.exists()
