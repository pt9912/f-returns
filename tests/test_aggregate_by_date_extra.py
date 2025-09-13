import pandas as pd

from rolling_returns.legacy.depotex import aggregate_by_date


def test_aggregate_by_date_last_vs_sum():
    df = pd.DataFrame(
        [
            {
                "Date": "2024-01-01",
                "End_NAV": 100.0,
                "Cash_Flow": 1.0,
                "Fee_Internal": 0.1,
                "Fee_External": 0.2,
                "Tax_Internal": 0.0,
            },
            {
                "Date": "2024-01-01",
                "End_NAV": 101.0,
                "Cash_Flow": 2.0,
                "Fee_Internal": 0.3,
                "Fee_External": 0.4,
                "Tax_Internal": 0.5,
            },
        ]
    )
    out = aggregate_by_date(df)
    assert float(out.loc[0, "End_NAV"]) == 101.0  # last of the day
    assert float(out.loc[0, "Cash_Flow"]) == 3.0
    assert float(out.loc[0, "Fee_Internal"]) == 0.4
    import pytest

    assert float(out.loc[0, "Fee_External"]) == pytest.approx(0.6)
    assert float(out.loc[0, "Tax_Internal"]) == 0.5


def test_aggregate_by_date_no_known_columns_returns_input():
    df = pd.DataFrame([{"Date": "2024-01-01", "Other": 1}, {"Date": "2024-01-01", "Other": 2}])
    out = aggregate_by_date(df)
    # Since none of the known columns are present, function should return df unchanged
    assert out.equals(df)
