import importlib

import numpy as np
import pandas as pd
import pytest

# Skip if numpy_financial is not installed; this test targets the 'except Exception' branch inside xirr call
numpy_financial = importlib.util.find_spec("numpy_financial")
pytestmark = pytest.mark.skipif(
    numpy_financial is None, reason="requires numpy_financial installed"
)

from rolling_returns.legacy.depot import _xirr_series


def test_xirr_series_exception_branch_sets_nan():
    # Construct a window where xirr will raise (e.g., all cash flows zero and NAV strictly positive, no sign change)
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-02", "End_NAV": 101.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-03", "End_NAV": 102.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-04", "End_NAV": 103.0, "Cash_Flow": 0.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    s = _xirr_series(df, window=2, business_days=False)
    # We expect at least one NaN produced from the except path
    assert s.isna().any()
