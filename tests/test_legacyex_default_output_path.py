# tests/test_legacyex_default_output_path.py
from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depotex import run_legacy


def test_legacyex_default_output_path(tmp_path: Path):
    csv = tmp_path / "combined.csv"
    pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "End_NAV": [100, 101, 102],
            "Cash_Flow": [0, 0, 0],
        }
    ).to_csv(csv, index=False)

    # output=None -> triggert Default-Pfad (…/combined_with_returns.csv)
    res = run_legacy(csv_file=csv, output=None, plot=False)
    out_path = res["out_path"]
    assert out_path.name == "combined_with_returns.csv"
    assert out_path.parent == csv.parent
    assert out_path.exists()


def test_legacyex_default_output_with_prefix(tmp_path: Path):
    csv = tmp_path / "nav.csv"
    pd.DataFrame({"Date": ["2024-01-01"], "End_NAV": [100], "Cash_Flow": [0]}).to_csv(
        csv, index=False
    )
    target = tmp_path / "subdir"
    res = run_legacy(csv_file=csv, output=None, output_prefix=target, plot=False)
    assert res["out_path"].parent == target


def test_run_legacy_nav_and_flows_files(tmp_path: Path):
    flows_file = tmp_path / "flows.csv"
    flows = [
        {"Date": "2024-01-01", "Cash_Flow": -100.0},
        {"Date": "2024-01-03", "Cash_Flow": 30.0},
    ]
    pd.DataFrame(flows).to_csv(flows_file, index=False, sep=",", decimal=".")
    nav_file = tmp_path / "navws.csv"
    nav = [
        {"Date": "2024-01-01", "End_NAV": 1000.0},
        {"Date": "2024-01-02", "End_NAV": 1005.0},
        {"Date": "2024-01-03", "End_NAV": 990.0},
    ]
    pd.DataFrame(nav).to_csv(nav_file, index=False, sep=",", decimal=".")

    target = tmp_path / "subdir"
    res = run_legacy(
        csv_file=None,
        nav_file=nav_file,
        flows_file=flows_file,
        window=2,
        business_days=True,
        annualize=False,
        money_weighted=False,
        include_tax=False,
        plot=False,
        output_prefix=target,  # ensure output goes to tmp
    )
    assert res["out_path"].parent == target
