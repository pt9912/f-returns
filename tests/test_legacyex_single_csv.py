from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depotex import run_legacy


def test_legacyex_single_csv_input(tmp_path: Path):
    df = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "End_NAV": [100, 101, 102],
            "Cash_Flow": [0, -5, 3],
            "Fee_Internal": [0, 0.5, 0],
            "Tax_Internal": [0, 0.4, 0],
        }
    )
    csv = tmp_path / "combined.csv"
    df.to_csv(csv, index=False)
    out = tmp_path / "out.csv"
    res = run_legacy(
        csv_file=csv, nav_file=None, flows_file=None, output=out, plot=False, save_svg=False
    )
    assert out.exists()
    assert "df" in res and not res["df"].empty
