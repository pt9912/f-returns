from pathlib import Path

import pandas as pd
import pytest

from rolling_returns.legacy.depotex import run_legacy


def test_depotex_run_legacy_raises_when_no_inputs():
    with pytest.raises(SystemExit):
        run_legacy(csv_file=None, nav_file=None, flows_file=None)


def test_depotex_run_legacy_nav_missing_end_nav(tmp_path: Path):
    nav = pd.DataFrame([{"Date": "2024-01-01", "X": 1}])
    p = tmp_path / "nav.csv"
    nav.to_csv(p, index=False)
    with pytest.raises(ValueError):
        run_legacy(csv_file=None, nav_file=p, flows_file=None)


def test_depotex_run_legacy_flows_missing_cash_flow(tmp_path: Path):
    fl = pd.DataFrame([{"Date": "2024-01-01", "X": 1}])
    p = tmp_path / "flows.csv"
    fl.to_csv(p, index=False)
    with pytest.raises(ValueError):
        run_legacy(csv_file=None, nav_file=None, flows_file=p)


def test_depotex_run_legacy_date_coercion(tmp_path: Path):
    nav = pd.DataFrame(
        [
            {"Date": "2024/01/01", "End_NAV": 100.0},
            {"Date": "2024/01/02", "End_NAV": 101.0},
        ]
    )
    p = tmp_path / "nav.csv"
    nav.to_csv(p, index=False)
    res = run_legacy(csv_file=None, nav_file=p, flows_file=None)
    # Wenn es ohne Exception durchläuft, wurde die Date-Koerzierung ausgeführt.
    assert "out_path" in res and "df" in res
