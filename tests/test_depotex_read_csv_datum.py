from pathlib import Path

import pandas as pd

from rolling_returns.legacy.depotex import read_csv_generic


def test_depotex_read_csv_generic_uses_datum_branch(tmp_path: Path):
    p = tmp_path / "in.csv"
    pd.DataFrame([{"Datum": "2024-02-01", "Wert": 123.0, "Einzahlung": 5.0}]).to_csv(
        p, index=False, sep=";", decimal=","
    )
    df = read_csv_generic(p, sep=";", dec=",")
    assert "Date" in df.columns and str(df.loc[0, "Date"].date()) == "2024-02-01"
