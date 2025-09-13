from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depot import run_legacy as run_legacy_simple
from rolling_returns.legacy.depotex import run_legacy as run_legacy_ex


def test_legacy_plot_and_svg(tmp_path: Path, monkeypatch):
    # small NAV series
    csv = tmp_path / "legacy.csv"
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "End_NAV": [100, 101, 103, 104],
            "Cash_Flow": [0, 0, 0, 0],
            "Fee_Internal": [0, 0, 0, 0],
            "Tax_Internal": [0, 0, 0, 0],
        }
    ).to_csv(csv, index=False)
    out = tmp_path / "out.csv"
    res = run_legacy_simple(csv_file=csv, output=out, plot=True, save_svg=True)
    assert out.exists()
    # ensure some plot got saved next to output (png or svg path is internal; just check dir)
    pngs = list(tmp_path.glob("*.png"))
    svgs = list(tmp_path.glob("*.svg"))
    assert pngs or svgs


def test_legacyex_plot_and_svg(tmp_path: Path):
    csv = tmp_path / "legacyex.csv"
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "End_NAV": [100, 101, 103, 104],
            "Cash_Flow": [0, 0, 0, 0],
        }
    ).to_csv(csv, index=False)
    out = tmp_path / "out_ex.csv"
    res = run_legacy_ex(csv_file=csv, output=out, plot=True, save_svg=True)
    assert out.exists()
    pngs = list(tmp_path.glob("*.png"))
    svgs = list(tmp_path.glob("*.svg"))
    assert pngs or svgs
