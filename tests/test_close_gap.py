import subprocess
import sys
from pathlib import Path

import pandas as pd


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _mk_legacy_csv(path: Path):
    df = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "End_NAV": 100.0,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-03",
                "End_NAV": 101.5,
                "Cash_Flow": -10.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-04",
                "End_NAV": 103.0,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
        ]
    )
    df.to_csv(path, index=False)


def _mk_legacyex_single_csv(path: Path):
    # Provide a combined CSV that should satisfy legacyex when no nav/flows are given
    df = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "End_NAV": 100.0,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-03",
                "End_NAV": 101.0,
                "Cash_Flow": -5.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-04",
                "End_NAV": 102.0,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
            },
        ]
    )
    df.to_csv(path, index=False)


def test_cli_legacy_smoke_v7(tmp_path: Path):
    legacy_csv = tmp_path / "legacy.csv"
    _mk_legacy_csv(legacy_csv)
    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "legacy",
            "--csv-file",
            str(legacy_csv),
            "--csv-in-sep",
            ",",
            "--csv-in-decimal",
            ".",
            "--csv-out-sep",
            ",",
            "--csv-out-decimal",
            ".",
            "--window",
            "5",
            "--business-days",
            "--annualize",
            "--money-weighted",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"


def test_cli_legacyex_smoke_v7(tmp_path: Path):
    base_csv = tmp_path / "base.csv"
    _mk_legacyex_single_csv(base_csv)
    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "legacyex",
            "--csv-file",
            str(base_csv),
            "--csv-in-sep",
            ",",
            "--csv-in-decimal",
            ".",
            "--csv-out-sep",
            ",",
            "--csv-out-decimal",
            ".",
            "--window",
            "5",
            "--business-days",
            "--annualize",
            "--money-weighted",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"


# ---------------- Legacy ----------------


def _mk_legacy_csv_with_external_tax(path: Path):
    df = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "End_NAV": 100.0,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
                "ExtTax": 0.5,
            },
            {
                "Date": "2024-01-03",
                "End_NAV": 101.5,
                "Cash_Flow": -10.0,
                "Fee_Internal": 0.2,
                "Tax_Internal": 0.0,
                "ExtTax": 0.0,
            },
            {
                "Date": "2024-01-04",
                "End_NAV": 103.0,
                "Cash_Flow": 0.0,
                "Fee_Internal": 0.0,
                "Tax_Internal": 0.0,
                "ExtTax": 0.1,
            },
        ]
    )
    df.to_csv(path, index=False)


def test_cli_legacy_external_tax_column_v9(tmp_path: Path):
    csv = tmp_path / "legacy_extax.csv"
    _mk_legacy_csv_with_external_tax(csv)
    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "legacy",
            "--csv-file",
            str(csv),
            "--external-tax-column",
            "ExtTax",
            "--csv-in-sep",
            ",",
            "--csv-in-decimal",
            ".",
            "--csv-out-sep",
            ",",
            "--csv-out-decimal",
            ".",
            "--window",
            "3",
            "--annualize",
            "--money-weighted",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"


# ---------------- LegacyEx ----------------


def _mk_nav_and_zero_flows(nav_path: Path, flows_path: Path, base_path: Path):
    nav = pd.DataFrame(
        [
            {"Date": "2024-01-02", "End_NAV": 100.0},
            {"Date": "2024-01-03", "End_NAV": 101.0},
            {"Date": "2024-01-04", "End_NAV": 102.0},
        ]
    )
    flows = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Cash_Flow": 0.0},
            {"Date": "2024-01-03", "Cash_Flow": 0.0},
            {"Date": "2024-01-04", "Cash_Flow": 0.0},
        ]
    )
    base = nav.merge(flows, on="Date", how="left")
    nav.to_csv(nav_path, index=False)
    flows.to_csv(flows_path, index=False)
    base.to_csv(base_path, index=False)


# ---------------- Returns / Pipeline ----------------


def test_cli_returns_nav_file_only_with_min_trade_v9(tmp_path: Path):
    # Provide nav-file and a minimal BUY trade so TWG has Date
    nav = pd.DataFrame(
        [
            {"Date": "2024-01-02", "End_NAV": 100.0},
            {"Date": "2024-01-03", "End_NAV": 101.0},
            {"Date": "2024-01-04", "End_NAV": 99.0},
        ]
    )
    nav_path = tmp_path / "nav.csv"
    nav.to_csv(nav_path, index=False)

    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "NAV_ONLY",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            }
        ]
    )
    tr = tmp_path / "trades.csv"
    trades.to_csv(tr, index=False)

    code, out, err = _run(
        [
            sys.executable,
            "-m",
            "rolling_returns.cli",
            "returns",
            "--trades-file",
            str(tr),
            "--nav-file",
            str(nav_path),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert code == 0, f"stdout={out}\nstderr={err}"
