import numpy as np
import pandas as pd

from rolling_returns.pipeline import compute_returns


def test_pipeline_mwr_handles_small_series():
    # Keine NaT im Index; monotone Zeitachse
    nav = pd.DataFrame(
        {
            "Date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")],
            "End_NAV": [100.0, 100.0],
        }
    )
    out = compute_returns(
        nav=nav,
        tax_cf=None,
        window=1,
        business_days=False,
        annualize=False,
        money_weighted=True,
    )
    # Es sollte ohne Fehler durchlaufen und die Spalte existieren.
    assert "Rolling_MWR" in out.columns
    # In der ersten Zeile ist i. d. R. kein vollständiges Fenster vorhanden -> NaN oder 0.
    assert pd.isna(out.loc[0, "Rolling_MWR"]) or out.loc[0, "Rolling_MWR"] == 0
