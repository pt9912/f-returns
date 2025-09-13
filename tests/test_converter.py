import pandas as pd

from rolling_returns.converter.generic import convert_prices_df, convert_trades_df


def test_convert_trades_df():
    df = pd.DataFrame(
        {
            "Buchungstag": ["2023-01-01"],
            "Vorgang": ["buy"],
            "Wertpapier": ["ABC"],
            "Typ": ["stock"],
            "Stueck": [10],
            "Kurs": [100.0],
            "Gebuehr": [1.0],
            "Steuer": [0.0],
            "Waehrung": ["EUR"],
        }
    )
    mapping = {
        "date": "Buchungstag",
        "action": "Vorgang",
        "symbol": "Wertpapier",
        "asset_type": "Typ",
        "qty": "Stueck",
        "price": "Kurs",
        "fee": "Gebuehr",
        "tax": "Steuer",
        "currency": "Waehrung",
    }
    out = convert_trades_df(df, mapping)
    assert out.loc[0, "Action"] == "BUY"
    assert out.loc[0, "Quantity"] == 10


def test_convert_prices_df():
    df = pd.DataFrame({"Datum": ["2023-01-01"], "Symbol": ["ABC"], "Schlusskurs": [101.0]})
    mapping = {"date": "Datum", "symbol": "Symbol", "close": "Schlusskurs"}
    out = convert_prices_df(df, mapping)
    assert out.loc[0, "ClosePrice"] == 101.0
