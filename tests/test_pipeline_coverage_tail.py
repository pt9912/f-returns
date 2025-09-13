# tests/test_pipeline_coverage_tail.py
import pandas as pd

from rolling_returns.pipeline import compute_returns


def test_compute_returns_hits_mwr_annualize_branch():
    # Minimaler DF mit Cash_Flow, damit money_weighted-Pfad aktiv ist
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-04", "End_NAV": 101.0, "Cash_Flow": 0.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])

    out = compute_returns(
        df,
        tax_cf=None,
        window=2,  # kleines Fenster
        business_days=False,  # Datumsbasiert
        annualize=True,  # annualize-Zweig
        money_weighted=True,  # MWR + MWR_Ann erzeugen
    )
    assert "Rolling_MWR_Ann" in out.columns
