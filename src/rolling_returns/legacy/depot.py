"""
Legacy-Modul für die Berechnung rollierender Renditen (TWR/MWR) aus CSV-Dateien.

Dieses Modul bietet Funktionen zur Berechnung von:
- Zeitgewichteten Renditen (TWR)
- Geldgewichteten Renditen (MWR, XIRR)
- Gebühren- und Steuerbereinigung
- Annualisierung von Renditen

Funktionen:
- _normalize_columns: Normalisiert Spaltennamen in DataFrames.
- _compute_twr: Berechnet rollierende TWR-Renditen.
- _xirr_series: Berechnet rollierende MWR-Renditen via XIRR.
- _annualize: Annualisiert Renditen.
- run_legacy: Hauptfunktion zur Verarbeitung von Legacy-CSV-Dateien.

Abhängigkeiten:
- pandas, numpy, numpy_financial (optional für MWR), matplotlib (optional für Plots)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

ALIASES: dict[str, list[str]] = {
    "Date": ["Date", "Datum"],
    "End_NAV": ["End_NAV", "Depotwert", "Portfolio Value", "Wert"],
    "Cash_Flow": ["Cash_Flow", "Einzahlung", "Auszahlung", "Flows", "Cashflow", "Cash Flow"],
    "Fee_Internal": [
        "Fee_Internal",
        "Gebuehren",
        "Gebühren",
        "Intern_Gebuehr",
        "Intern_Gebühr",
        "Kosten_intern",
    ],
    "Tax_Internal": [
        "Tax_Internal",
        "Steuer_intern",
        "Quellensteuer",
        "Kapitalertragsteuer_intern",
    ],
}

logger = logging.getLogger(__name__)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalisiert Spaltennamen anhand der ALIASES-Mapping-Tabelle.

    Args:
        df: Input-DataFrame mit beliebigen Spaltennamen.

    Returns:
        pd.DataFrame: DataFrame mit standardisierten Spaltennamen.
    """
    rename_map = {}
    lower_cols = {c.lower(): c for c in df.columns}
    for std_col, alternatives in ALIASES.items():
        for alt in alternatives:
            if alt in df.columns:
                rename_map[alt] = std_col
                break
            if alt.lower() in lower_cols:
                rename_map[lower_cols[alt.lower()]] = std_col
                break
    return df.rename(columns=rename_map)


def _compute_twr(
    df: pd.DataFrame, window: int, business_days: bool, nav_col: str = "End_NAV"
) -> pd.Series:
    """Berechnet rollierende Time-Weighted Returns (TWR).

    Args:
        df: DataFrame mit "Date", "End_NAV" und optional "Cash_Flow".
        window: Fenstergröße (Tage).
        business_days: Nur Handelstage berücksichtigen.
        nav_col: Spaltenname für NAV (Default: "End_NAV").

    Returns:
        pd.Series: TWR-Zeitreihe (gleicher Index wie df).
    """
    end_nav = df[nav_col].astype(float)
    prev_nav = end_nav.shift(1)
    cash_flow = df.get("Cash_Flow", pd.Series(0.0, index=df.index)).fillna(0.0)
    daily_r = (end_nav - cash_flow) / prev_nav - 1.0
    daily_r.iloc[0] = np.nan
    if business_days:
        return (1.0 + daily_r).rolling(window=window, min_periods=window).apply(
            np.prod, raw=True
        ) - 1.0
    s = (1.0 + daily_r).copy()
    s.index = pd.to_datetime(df["Date"])
    return s.rolling(window=f"{window}D").apply(np.prod, raw=True).reindex(s.index) - 1.0


def _xirr_series(df: pd.DataFrame, window: int, business_days: bool) -> pd.Series:
    """Berechnet rollierende Money-Weighted Returns (MWR) via XIRR.

    Args:
        df: DataFrame mit "Date", "End_NAV" und "Cash_Flow".
        window: Fenstergröße (Tage).
        business_days: Nur Handelstage berücksichtigen.

    Returns:
        pd.Series: MWR-Zeitreihe (gleicher Index wie df).
                   NaN, falls numpy_financial fehlt.
    """
    try:
        import numpy_financial as npf
    except ImportError:
        logger.warning("numpy-financial fehlt: MWR wird übersprungen.")
        return pd.Series(np.nan, index=df.index, dtype=float)
    irr = pd.Series(np.nan, index=df.index, dtype=float)
    for i in range(len(df)):
        if business_days and i < window:
            continue
        if business_days:
            # fmt: off
            window_df = df.iloc[max(0, i - window + 1): i + 1]  # noqa: E203
            # fmt: on
        else:
            end_date = df.at[i, "Date"]
            start_date = end_date - pd.Timedelta(days=window)
            window_df = df[(df["Date"] > start_date) & (df["Date"] <= end_date)]
        if window_df.empty:
            continue
        cash_flows = (-window_df["Cash_Flow"].astype(float)).tolist()
        cash_flows.append(float(window_df.iloc[-1]["End_NAV"]))
        dates = window_df["Date"].tolist()
        try:
            irr.iloc[i] = npf.xirr(cash_flows, dates)
        except Exception:
            irr.iloc[i] = np.nan
    return irr


def _annualize(returns: pd.Series, window: int) -> pd.Series:
    """Annualisiert Renditen: (1 + R)^(365/window) - 1.

    Args:
        returns: Serie mit Renditen (z. B. TWR oder MWR).
        window: Fenstergröße (Tage).

    Returns:
        pd.Series: Annualisierte Renditen.
    """
    with np.errstate(invalid="ignore"):
        return (1.0 + returns) ** (365.0 / float(window)) - 1.0


def run_legacy(
    *,
    csv_file: Path,
    external_tax_column: str | None = None,
    csv_in_sep: str = ",",
    csv_in_decimal: str = ".",
    csv_out_sep: str = ",",
    csv_out_decimal: str = ".",
    window: int = 252,
    business_days: bool = False,
    annualize: bool = False,
    money_weighted: bool = False,
    plot: bool = False,
    save_svg: bool = False,
    output: Path | None = None,
    output_prefix: Path | None = None,
) -> Dict[str, Any]:
    """Hauptfunktion: Verarbeitet Legacy-CSV und generiert Returns-Metriken.

    Args:
        args: ArgumentParser-Namespace mit Parametern:
            - csv_file: Input-CSV-Pfad
            - csv_in_sep: Trennzeichen (Default: ",")
            - csv_in_decimal: Dezimaltrennzeichen (Default: ".")
            - window: Rollierendes Fenster (Default: 252)
            - business_days: Nur Handelstage (Default: False)
            - annualize: Annualisierung (Default: False)
            - money_weighted: MWR berechnen (Default: False)
            - external_tax_column: Spalte für externe Steuern (optional)
            - plot: Plot generieren (Default: False)
            - save_svg: SVG zusätzlich speichern (Default: False)
            - output: Output-Pfad (optional)

    Returns:
        Path: Pfad zur ausgegebenen CSV-Datei.

    Raises:
        ValueError: Falls erforderliche Spalten ("Date", "End_NAV") fehlen.
    """
    df = pd.read_csv(csv_file, sep=csv_in_sep, decimal=csv_in_decimal, parse_dates=["Date"])
    df = _normalize_columns(df)
    if "Date" not in df.columns or "End_NAV" not in df.columns:
        raise ValueError("Legacy-CSV benötigt mindestens 'Date' und 'End_NAV'.")
    df = df.sort_values("Date").reset_index(drop=True)

    if external_tax_column and external_tax_column in df.columns:
        df["Cash_Flow"] = df.get("Cash_Flow", 0.0).fillna(0.0) + df[external_tax_column].fillna(0.0)

    fees = df.get("Fee_Internal", 0.0).fillna(0.0)
    taxes = df.get("Tax_Internal", 0.0).fillna(0.0)
    if "Cash_Flow" not in df.columns:
        df["Cash_Flow"] = 0.0

    base_df = df[["Date", "End_NAV", "Cash_Flow"]].copy()
    base_df["Rolling_TWR"] = _compute_twr(base_df, window, business_days)

    df_ex = df.copy()
    df_ex["End_NAV"] = df["End_NAV"].astype(float) + fees + taxes
    exf_df = df_ex[["Date", "End_NAV", "Cash_Flow"]].copy()
    exf_df["Rolling_TWR_exFees"] = _compute_twr(exf_df, window, business_days)

    out = base_df.merge(exf_df[["Date", "Rolling_TWR_exFees"]], on="Date", how="left")
    out["TWR_FeeTax_Impact_pp"] = (out["Rolling_TWR"] - out["Rolling_TWR_exFees"]) * 100.0

    if money_weighted:
        out["Rolling_MWR"] = _xirr_series(base_df, window, business_days)

    if annualize:
        out["Rolling_TWR_Ann"] = _annualize(out["Rolling_TWR"], window)
        out["Rolling_TWR_exFees_Ann"] = _annualize(out["Rolling_TWR_exFees"], window)
        if "Rolling_MWR" in out.columns:
            out["Rolling_MWR_Ann"] = _annualize(out["Rolling_MWR"], window)

    # Gebühren/Steuern pro Fenster
    if business_days:
        out["Fee_Window_Sum"] = fees.rolling(window, min_periods=window).sum()
        out["Tax_Window_Sum"] = taxes.rolling(window, min_periods=window).sum()
    else:
        s_fee = fees.copy()
        s_fee.index = pd.to_datetime(df["Date"])
        s_tax = taxes.copy()
        s_tax.index = pd.to_datetime(df["Date"])
        out["Fee_Window_Sum"] = s_fee.rolling(f"{window}D").sum().reindex(s_fee.index).values
        out["Tax_Window_Sum"] = s_tax.rolling(f"{window}D").sum().reindex(s_tax.index).values

    # Output-Datei ableiten
    out_path = Path(output) if output else Path(f"{csv_file.stem}_with_returns.csv")
    if output_prefix:
        out_path = Path(output_prefix) / out_path.name

    out.to_csv(out_path, index=False, float_format="%.6f", sep=csv_out_sep, decimal=csv_out_decimal)
    logger.info(f"Legacy-Ergebnis gespeichert: {out_path}")

    # Plot (optional)
    if plot:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))
        plt.plot(
            out["Date"],
            out["Rolling_TWR"] * 100.0,
            label="TWR (netto)",
            linewidth=1.5,
            color="tab:blue",
        )
        plt.plot(
            out["Date"],
            out["Rolling_TWR_exFees"] * 100.0,
            label="TWR ohne interne Gebühren/Steuern",
            linestyle="--",
            color="tab:green",
        )
        if "Rolling_MWR" in out.columns:
            plt.plot(
                out["Date"],
                out["Rolling_MWR"] * 100.0,
                label="MWR (XIRR)",
                linestyle=":",
                color="tab:red",
            )
        plt.axhline(0, linewidth=0.8, linestyle=":", color="black")
        ttl = f"Rollierende {window}-{'Handels' if business_days else 'Kalender'}tage" + (
            " (annualisiert)" if annualize else ""
        )
        plt.title(ttl)
        plt.xlabel("Datum")
        plt.ylabel("Rendite [%]")
        plt.legend()
        plt.grid(alpha=0.3)
        png_path = out_path.with_suffix(".png")
        plt.tight_layout()
        plt.savefig(png_path, dpi=200)
        if save_svg:
            svg_path = out_path.with_suffix(".svg")
            plt.savefig(svg_path)
        plt.close()

    return {"out_path": out_path, "df": out, "fees": fees, "taxes": taxes}
