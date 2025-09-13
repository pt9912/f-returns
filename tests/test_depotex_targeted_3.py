from pathlib import Path

import pandas as pd

import rolling_returns.legacy.depotex as dx


def test_depotex_run_legacy_triggers_date_coercion(monkeypatch, tmp_path: Path):
    # Monkeypatch read_csv_generic, damit 'Date' als object/String zurückkommt -> Zeile 461 coerct zu datetime
    def fake_read_csv_generic(path, sep, dec):
        return pd.DataFrame([{"Date": "2024-01-01", "End_NAV": 100.0}])  # Date als string

    monkeypatch.setattr(dx, "read_csv_generic", fake_read_csv_generic)

    # nav_file als Path übergeben (run_legacy nutzt .stem)
    nav_path = tmp_path / "nav.csv"
    res = dx.run_legacy(csv_file=None, nav_file=nav_path, flows_file=None)
    df = res["df"]
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
