import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def test_cli_returns_plot_and_svg(tmp_path: Path):
    # minimal trades + nav, request plotting and svg saving
    nav = pd.DataFrame(
        [
            {"Date": "2024-01-02", "End_NAV": 100.0},
            {"Date": "2024-01-03", "End_NAV": 101.0},
            {"Date": "2024-01-04", "End_NAV": 102.0},
            {"Date": "2024-01-05", "End_NAV": 104.0},
        ]
    )
    tr = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "N",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    nav_file = tmp_path / "nav.csv"
    tr_file = tmp_path / "trades.csv"
    nav.to_csv(nav_file, index=False)
    tr.to_csv(tr_file, index=False)

    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "returns",
            "--trades-file",
            str(tr_file),
            "--nav-file",
            str(nav_file),
            "--base-currency",
            "EUR",
            "--window",
            "2",
            "--annualize",
            "--business-days",
            "--money-weighted",
            "--plot",
            "--save-svg",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"
    assert (tmp_path / "returns.png").exists()
    assert (tmp_path / "returns.svg").exists()
