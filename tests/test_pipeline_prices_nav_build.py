import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def test_cli_returns_prices_path_builds_nav(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "X",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-01-04",
                "Action": "SELL",
                "Instrument": "X",
                "Quantity": 1,
                "Price": 103.0,
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
            {"Date": "2024-01-03", "Instrument": "X", "ClosePrice": 101.0},
            {"Date": "2024-01-04", "Instrument": "X", "ClosePrice": 103.0},
        ]
    )
    fx = pd.DataFrame([{"Date": "2024-01-02", "From": "EUR", "To": "EUR", "Rate": 1.0}])

    tr = tmp_path / "trades.csv"
    pr = tmp_path / "prices.csv"
    fxp = tmp_path / "fx.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)
    fx.to_csv(fxp, index=False)

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
    # nav.csv should be created by the build_nav branch
    assert (tmp_path / "nav.csv").exists()
    assert (tmp_path / "trades_with_gains.csv").exists()
