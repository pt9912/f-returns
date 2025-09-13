import pandas as pd

from rolling_returns.pipeline import fifo_gains, fx_lookup


def make_fx():
    # Identity FX EUR->EUR=1.0 default
    import pandas as pd

    return pd.DataFrame([{"Date": "2024-01-01", "CCY": "EUR", "Base": "EUR", "Rate": 1.0}])


def test_fifo_partial_lot_update_and_followup_sell():
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "X",
                "Quantity": 10.0,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-01-10",
                "Action": "BUY",
                "Instrument": "X",
                "Quantity": 5.0,
                "Price": 120.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-01",
                "Action": "SELL",
                "Instrument": "X",
                "Quantity": 12.0,
                "Price": 130.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-05",
                "Action": "SELL",
                "Instrument": "X",
                "Quantity": 3.0,
                "Price": 130.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    fx = make_fx()
    out = fifo_gains(trades, fx, "EUR")
    # First SELL: consumes 10@100 + 2@120 => cost=1240, proceeds=1560, gain=320
    g1 = float(out.loc[out["Date"] == "2024-02-01", "Realized_Gain_Base"].iloc[0])
    assert abs(g1 - 320.0) < 1e-9
    # Second SELL: remaining 3@120 => cost=360, proceeds=390, gain=30
    g2 = float(out.loc[out["Date"] == "2024-02-05", "Realized_Gain_Base"].iloc[0])
    assert abs(g2 - 30.0) < 1e-9
