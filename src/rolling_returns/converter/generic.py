"""
converters.generic - Konverter-Framework für Broker-Exports.

Konverter-Framework für Broker-Exports.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

# Standard-Mappings für Trades und Prices
DEFAULT_TRADE_MAP: Dict[str, str] = {
    "date": "Date",
    "action": "Action",
    "symbol": "Instrument",
    "asset_type": "AssetType",
    "qty": "Quantity",
    "price": "Price",
    "fee": "Fees",
    "tax": "Tax",
    "currency": "Currency",
}

DEFAULT_PRICE_MAP: Dict[str, str] = {
    "date": "Date",
    "symbol": "Instrument",
    "close": "ClosePrice",
}

# Normalisierung der Aktionen (z. B. "buy" → "BUY")
ACTIONS_NORMALIZE: Dict[str, str] = {
    "buy": "BUY",
    "sell": "SELL",
    "div": "DIV",
    "fee": "FEE",
    "tax": "TAX",
}


def convert_trades_df(df: pd.DataFrame, mapping: Dict[str, Any]) -> pd.DataFrame:
    """Konvertiert einen Broker-spezifischen Trades-DataFrame in das Standardformat.

    Args:
        df: Input-DataFrame mit Broker-spezifischen Spalten.
        mapping: Dictionary zur Spaltenzuordnung (überschreibt DEFAULT_TRADE_MAP).

    Returns:
        pd.DataFrame: Standardisierter DataFrame mit Spalten:
            - Date (datetime64)
            - Action (str, z. B. "BUY", "SELL")
            - Instrument (str)
            - AssetType (str, Default: "stock")
            - Quantity (float)
            - Price (float)
            - Fees (float)
            - Tax (float)
            - Currency (str, Default: "EUR")

    Notes:
        - Fehlende Spalten werden mit Default-Werten gefüllt (z. B. Quantity=0.0).
        - Ungültige Datumsangaben werden entfernt (dropna).
    """
    m = {**DEFAULT_TRADE_MAP, **mapping}
    out = pd.DataFrame()

    # Datumskonvertierung (coerce → ungültige Datumsangaben werden NaT)
    out["Date"] = pd.to_datetime(df[m["date"]], errors="coerce")

    # Aktionen normalisieren (z. B. "buy" → "BUY")
    out["Action"] = (
        df[m["action"]]
        .astype(str)
        .str.lower()
        .map(ACTIONS_NORMALIZE)
        .fillna(df[m["action"]].astype(str).str.upper())
    )

    # Instrument und AssetType
    out["Instrument"] = df[m["symbol"]].astype(str)
    out["AssetType"] = (
        df[m["asset_type"]].astype(str).str.lower() if m["asset_type"] in df.columns else "stock"
    )

    # Numerische Spalten mit Default-Werten
    out["Quantity"] = pd.to_numeric(df.get(m["qty"], 0), errors="coerce").fillna(0.0)
    out["Price"] = pd.to_numeric(df.get(m["price"], 0), errors="coerce").fillna(0.0)
    out["Fees"] = pd.to_numeric(df.get(m["fee"], 0), errors="coerce").fillna(0.0)
    out["Tax"] = pd.to_numeric(df.get(m["tax"], 0), errors="coerce").fillna(0.0)

    # Währung (Default: "EUR")
    out["Currency"] = df.get(m["currency"], "EUR").astype(str)

    # Ungültige Zeilen (ohne Datum) entfernen
    return out.dropna(subset=["Date"])


def convert_prices_df(df: pd.DataFrame, mapping: Dict[str, Any]) -> pd.DataFrame:
    """Konvertiert einen Broker-spezifischen Prices-DataFrame in das Standardformat.

    Args:
        df: Input-DataFrame mit Broker-spezifischen Spalten.
        mapping: Dictionary zur Spaltenzuordnung (überschreibt DEFAULT_PRICE_MAP).

    Returns:
        pd.DataFrame: Standardisierter DataFrame mit Spalten:
            - Date (datetime64)
            - Instrument (str)
            - ClosePrice (float)

    Notes:
        - Zeilen ohne Datum, Instrument oder Preis werden entfernt.
    """
    m = {**DEFAULT_PRICE_MAP, **mapping}
    out = pd.DataFrame()

    out["Date"] = pd.to_datetime(df[m["date"]], errors="coerce")
    out["Instrument"] = df[m["symbol"]].astype(str)
    out["ClosePrice"] = pd.to_numeric(df[m["close"]], errors="coerce")

    # Ungültige Zeilen entfernen
    return out.dropna(subset=["Date", "Instrument", "ClosePrice"])
