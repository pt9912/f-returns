import sys
import types
from types import ModuleType

import numpy as np
import pandas as pd

from rolling_returns.legacy.depotex import rolling_mwr_xirr


def test_depotex_rolling_mwr_exception_sets_nan(monkeypatch):
    # Shim numpy_financial.xirr -> wirft Exception, um except-Pfad (Zeilen 348-349) zu treffen.
    mod = ModuleType("numpy_financial")

    def xirr(cash, dates):
        raise RuntimeError("boom")

    mod.xirr = xirr
    sys.modules["numpy_financial"] = mod

    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": -100.0},
            {"Date": "2024-01-02", "End_NAV": 101.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-03", "End_NAV": 102.0, "Cash_Flow": 0.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    out = rolling_mwr_xirr(df, window=2, business_days=False, include_tax=False)
    assert np.isnan(out.iloc[-1])
