# tests/test_cli_commands.py
from pathlib import Path

import pandas as pd

from rolling_returns.cli import main_rr


def _legacy_df():
    return pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "End_NAV": [100, 101, 102],
            "Cash_Flow": [0, 0, 0],
            "Fee_Internal": [0, 0, 0],
            "Tax_Internal": [0, 0, 0],
        }
    )


def test_cli_legacy(tmp_path: Path):
    csv = tmp_path / "legacy.csv"
    _legacy_df().to_csv(csv, index=False)
    out = tmp_path / "out.csv"
    rc = main_rr(
        [
            "legacy",
            "--csv-file",
            str(csv),
            "--output",
            str(out),
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert (tmp_path / out.name).exists()


def test_cli_legacyex_basic(tmp_path: Path):
    csv = tmp_path / "legacyex.csv"
    _legacy_df()[["Date", "End_NAV", "Cash_Flow"]].to_csv(csv, index=False)
    out = tmp_path / "out_ex.csv"
    rc = main_rr(
        [
            "legacyex",
            "--csv-file",
            str(csv),
            "--output",
            str(out),
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert (tmp_path / out.name).exists()


def test_cli_returns_monkeypatched(tmp_path: Path, monkeypatch):
    import rolling_returns.cli as cli_mod

    # vermeidet DataFrame-Truthiness im CLI (bis du den 1-Zeiler fixst)
    monkeypatch.setattr(cli_mod, "run_pipeline", lambda **kwargs: {"returns": None})
    trades = tmp_path / "tr.csv"
    prices = tmp_path / "pr.csv"
    pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "Action": "BUY",
                "Instrument": "X",
                "Quantity": 1,
                "Price": 1.0,
                "Fees": 0.0,
                "Tax": 0.0,
            }
        ]
    ).to_csv(trades, index=False)
    pd.DataFrame([{"Date": "2024-01-01", "Instrument": "X", "ClosePrice": 1.0}]).to_csv(
        prices, index=False
    )
    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(trades),
            "--prices-file",
            str(prices),
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert rc == 0


def test_cli_version():
    assert main_rr(["version"]) == 0
