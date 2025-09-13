from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depotex import read_csv_generic


def test_read_csv_generic_aliases_and_date(tmp_path: Path):
    p = tmp_path / "in.csv"
    # Use German aliases to trigger renames
    df = pd.DataFrame([{"Datum": "2024-01-02", "Wert": 100.0, "Einzahlung": 1.0}])
    df.to_csv(p, index=False, sep=";", decimal=",")
    out = read_csv_generic(p, sep=";", dec=",")
    assert "Date" in out.columns and "End_NAV" in out.columns and "Cash_Flow" in out.columns
    assert str(out.loc[0, "Date"].date()) == "2024-01-02"


def test_read_csv_generic_missing_date_raises(tmp_path: Path):
    p = tmp_path / "in.csv"
    pd.DataFrame([{"X": 1}]).to_csv(p, index=False)
    import pytest

    with pytest.raises(ValueError):
        read_csv_generic(p, sep=",", dec=".")
