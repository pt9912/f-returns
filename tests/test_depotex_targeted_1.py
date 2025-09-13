from pathlib import Path

import pandas as pd

import rolling_returns.legacy.depotex as dx


def test_depotex_read_csv_generic_datum_fallback(tmp_path: Path, monkeypatch):
    # Monkeypatch normalize_columns to an identity function so 'Datum' is NOT normalized to 'Date'.
    monkeypatch.setattr(dx, "normalize_columns", lambda df, aliases: df)
    p = tmp_path / "in.csv"
    pd.DataFrame([{"Datum": "2024-03-01", "Wert": 10.0}]).to_csv(
        p, index=False, sep=";", decimal=","
    )
    out = dx.read_csv_generic(p, sep=";", dec=",")
    # Fallback-Zweig muss 'Datum' -> 'Date' mappen und to_datetime anwenden
    assert "Date" in out.columns and pd.api.types.is_datetime64_any_dtype(out["Date"])
