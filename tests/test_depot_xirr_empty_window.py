import pandas as pd

from rolling_returns.legacy.depot import _xirr_series


def test_depot_xirr_empty_window_continue_branch():
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": 0.0},
            {
                "Date": None,
                "End_NAV": 101.0,
                "Cash_Flow": 0.0,
            },  # NaT -> leeres Zeitfenster beim date-basierten Modus
            {"Date": "2024-01-03", "End_NAV": 102.0, "Cash_Flow": 0.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    s = _xirr_series(df, window=2, business_days=False)
    # nur Sicherstellen, dass die Serie berechnet wurde
    assert len(s) == len(df)
