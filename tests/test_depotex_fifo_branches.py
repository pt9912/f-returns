import pandas as pd

from rolling_returns.legacy.depotex import calculate_fifo_cost_basis


def test_depotex_fifo_continue_without_cash_flow():
    df = pd.DataFrame([{"Date": "2024-01-01", "End_NAV": 100.0}])
    df["Date"] = pd.to_datetime(df["Date"])
    s = calculate_fifo_cost_basis(df)
    assert s.iloc[0] == 0.0


def test_depotex_fifo_pop_branch_on_full_consumption():
    # Kauf 100 -> Verkauf 100 (volle Entnahme -> pop)
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "End_NAV": 100.0, "Cash_Flow": -100.0},
            {"Date": "2024-01-02", "End_NAV": 100.0, "Cash_Flow": 100.0},
        ]
    )
    df["Date"] = pd.to_datetime(df["Date"])
    s = calculate_fifo_cost_basis(df)
    # steuerpflichtiger Gewinn = Auszahlung - Cost Basis (hier 0, da NAV==Investition)
    assert s.iloc[-1] >= 0.0
