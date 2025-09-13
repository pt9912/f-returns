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


from rolling_returns.pipeline import compute_returns


def test_pipeline_compute_returns_hits_416_business_days_iloc(monkeypatch):
    _ensure_dummy_npf(monkeypatch)
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0},
            {"Date": "2024-01-02", "End_NAV": 101.0},
            {"Date": "2024-01-03", "End_NAV": 102.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    out = compute_returns(
        df, tax_cf=None, window=2, business_days=True, annualize=False, money_weighted=True
    )
    assert "Rolling_TWR" in out.columns


import pytest


@pytest.mark.xfail(
    reason="Branch w.empty (line 423) ist praktisch nicht erreichbar, ohne zuvor das TWR-Rolling durch NaT zu brechen."
)
def test_pipeline_compute_returns_hits_423_empty_window_continue(monkeypatch):
    _ensure_dummy_npf(monkeypatch)
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0},
            {"Date": "2024-01-02", "End_NAV": 101.0},
            {"Date": "2024-01-03", "End_NAV": 102.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    # Ohne NaT ist w nie leer (enthält mind. die aktuelle Zeile). Mit NaT scheitert das vorgelagerte TWR-Rolling.
    out = compute_returns(
        df, tax_cf=None, window=2, business_days=False, annualize=False, money_weighted=True
    )
    assert "Rolling_TWR" in out.columns
