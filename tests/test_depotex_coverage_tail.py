# tests/test_depotex_coverage_tail.py
import pandas as pd

import rolling_returns.legacy.depotex as dx


def test_run_legacy_business_days_window_downsizes(monkeypatch, tmp_path):
    # kleinster NAV-DF: len(df)=2  -> window>=len(df) löst den Branch aus
    def fake_read_csv_generic(path, sep, dec):
        return pd.DataFrame(
            [
                {"Date": "2024-01-01", "End_NAV": 100.0},
                {"Date": "2024-01-02", "End_NAV": 101.0},
            ]
        )

    monkeypatch.setattr(dx, "read_csv_generic", fake_read_csv_generic)

    out = dx.run_legacy(
        csv_file=None,
        nav_file=str(tmp_path / "nav.csv"),
        flows_file=None,
        business_days=True,
        window=10,  # >= len(df) => Branch
    )
    # Sanity-Check: es kommt ein DataFrame zurück
    assert "df" in out and not out["df"].empty
