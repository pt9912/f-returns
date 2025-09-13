import numpy as np
import pandas as pd

from rolling_returns.legacy.depot import _xirr_series


def test_xirr_series_importerror_returns_nan_series():
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-02", "End_NAV": 101.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-03", "End_NAV": 99.0, "Cash_Flow": 0.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    s = _xirr_series(df, window=2, business_days=False)
    assert s.isna().all()
