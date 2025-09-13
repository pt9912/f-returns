# tests/test_legacyex_module.py
from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depotex import run_legacy


def test_legacyex_run_basic(tmp_path: Path):
    csv = tmp_path / "legacyex.csv"
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "End_NAV": [100, 101, 102],
            "Cash_Flow": [0, 0, 0],
        }
    ).to_csv(csv, index=False)
    out = tmp_path / "out.csv"
    res = run_legacy(csv_file=csv, output=out, plot=False)
    assert out.exists()
    assert "df" in res and not res["df"].empty
