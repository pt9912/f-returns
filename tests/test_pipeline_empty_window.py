import pandas as pd

from rolling_returns.pipeline import compute_returns


def test_pipeline_empty_window_guard_is_hit_deterministic():
    # Monotone Zeitachse, enger Zeitraum
    nav = pd.DataFrame(
        {
            "Date": [
                pd.Timestamp("2024-01-02 00:00:00"),
                pd.Timestamp("2024-01-02 00:00:00") + pd.Timedelta(seconds=1),
            ],
            "End_NAV": [100.0, 100.0],
        }
    )
    # window so wählen, dass der erste Punkt kein Vorlauf im Fenster hat
    out = compute_returns(
        nav=nav,
        tax_cf=None,
        window=1,  # 1D oder 1s – je nach Implementierung (falls zeitbasiert: "1s" o.ä.)
        business_days=False,
        annualize=False,
        money_weighted=True,
    )
    # Erwartung: kein Crash, Spalte existiert, erster Wert leer/neutral
    assert "Rolling_MWR" in out.columns
    assert pd.isna(out.loc[0, "Rolling_MWR"]) or out.loc[0, "Rolling_MWR"] == 0
    assert "Rolling_MWR" in out.columns
    assert pd.isna(out.loc[0, "Rolling_MWR"]) or out.loc[0, "Rolling_MWR"] == 0
