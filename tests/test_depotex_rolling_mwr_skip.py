import sys
import types
from types import ModuleType

import pandas as pd


def _ensure_dummy_npf(monkeypatch=None):
    mod = ModuleType("numpy_financial")

    def xirr(cash, dates):
        return float("nan")

    mod.xirr = xirr
    sys.modules["numpy_financial"] = mod


from rolling_returns.legacy.depotex import rolling_mwr_xirr


def test_depotex_rolling_mwr_skip_when_no_cash_flow(monkeypatch):
    _ensure_dummy_npf(monkeypatch)
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0},
            {"Date": "2024-01-02", "End_NAV": 101.0},
            {"Date": "2024-01-03", "End_NAV": 102.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    out = rolling_mwr_xirr(df, window=2, business_days=False, include_tax=False)
    assert len(out) == len(df)
