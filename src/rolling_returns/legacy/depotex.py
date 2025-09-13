"""
Rollierende Rendite für ein Depot (v1.6).

Features:
- Zeitgewichtete Rendite (TWR): simple oder flussbereinigt (chain-linked)
- Geldgewichtete Rendite (MWR, XIRR) pro Fenster
- Fenster als Kalendertage **oder** als Handelstage (--business-days)
- Flexible Eingabe:
    * eine Gesamt-CSV (Date, End_NAV [, Cash_Flow] [, Fee_Internal] [, Fee_External] [, Tax_Internal])
    * oder zwei Dateien: --nav-file (Date, End_NAV) und --flows-file (Date, Cash_Flow)
- **Steuerberechnung** (Deutschland):
    * FIFO-Besteuerung für realisierte Gewinne
    * Freistellungsauftrag (--tax-allowance)
    * Kirchensteuer (--church-tax)
    * Kapitalertragsteuer + Soli (--tax-rate)
- **Gebühren**:
    * Interne Gebühren (bereits im End_NAV enthalten, nur Transparenz)
    * Externe Gebühren (reduzieren Cash_Flow direkt)
- **Ausweisung**:
    * Steuerpflichtige Erträge (Taxable_Income)
    * Gezahlte Steuern (Tax_Paid)
    * Fee-/Tax-bereinigte Renditen

Pakete (pip install):
    pandas matplotlib numpy-financial tqdm
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TWRMode = Literal["simple", "flow-adjusted"]

ALIASES: Dict[str, List[str]] = {
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
    "Fee_External": ["Fee_External", "Extern_Gebuehr", "Extern_Gebühr", "Kosten_extern"],
    "Tax_Internal": [
        "Tax_Internal",
        "Steuer_intern",
        "Quellensteuer",
        "Kapitalertragsteuer_intern",
    ],
}


def normalize_columns(df: pd.DataFrame, aliases: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Normalisiert die Spaltennamen eines DataFrames anhand der gegebenen Aliase.

    Args:
        df: Eingabe-DataFrame.
        aliases: Wörterbuch, das Standard-Spaltennamen auf mögliche Aliase abbildet.

    Returns:
        DataFrame mit normalisierten Spaltennamen.
    """
    rename_map = {}
    cols_lower = {c.lower(): c for c in df.columns}
    for std, alts in aliases.items():
        for alt in alts:
            if alt in df.columns:
                rename_map[alt] = std
                break
            if alt.lower() in cols_lower:
                rename_map[cols_lower[alt.lower()]] = std
                break
    return df.rename(columns=rename_map)


def read_csv_generic(path: Path, sep: str, dec: str) -> pd.DataFrame:
    """
    Liest eine CSV-Datei ein und normalisiert die Spaltennamen.

    Args:
        path: Pfad zur CSV-Datei.
        sep: Trennzeichen der CSV-Datei.
        dec: Dezimalzeichen der CSV-Datei.

    Returns:
        DataFrame mit normalisierten Spaltennamen und konvertierten Datumsangaben.
    """
    df = pd.read_csv(path, sep=sep, decimal=dec)
    df = normalize_columns(df, ALIASES)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif "Datum" in df.columns:
        df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
        df = df.rename(columns={"Datum": "Date"})
    if "Date" not in df.columns:
        raise ValueError(f"Date/Datum-Spalte fehlt in Datei: {path}")
    return df


def aggregate_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregiert die Daten eines DataFrames nach Datum.

    Für 'End_NAV' wird der letzte Wert pro Tag genommen,
    für alle anderen Spalten wird die Summe gebildet.

    Args:
        df: Eingabe-DataFrame mit Datums- und Wertespalten.

    Returns:
        Aggregierter DataFrame nach Datum.
    """
    agg = {}
    for col in ["End_NAV", "Cash_Flow", "Fee_Internal", "Fee_External", "Tax_Internal"]:
        if col in df.columns:
            if col == "End_NAV":
                agg[col] = "last"
            else:
                agg[col] = "sum"
    return df.groupby("Date", as_index=False).agg(agg) if agg else df


def calculate_tax_rate(
    base_rate: float = 0.25, soli: bool = True, church_tax: float = 0.0
) -> float:
    """
    Berechnet die effektive Steuerrate inkl. Soli und Kirchensteuer.

    Args:
        base_rate: Basissteuersatz (Standard: 0.25).
        soli: Ob Solidaritätszuschlag berücksichtigt wird (Standard: True).
        church_tax: Kirchensteuersatz (Standard: 0.0).

    Returns:
        Effektive Steuerrate.
    """
    capital_tax = base_rate
    if soli:
        capital_tax *= 1.055  # Soli-Zuschlag
    if church_tax > 0:
        capital_tax *= 1 + church_tax  # Kirchensteuer auf die Kapitalertragsteuer
    return capital_tax


def calculate_fifo_cost_basis(df: pd.DataFrame) -> pd.Series:
    """
    Berechnet steuerpflichtige Gewinne nach FIFO für Verkäufe.

    Annahme: Cash_Flow < 0 = Kauf, Cash_Flow > 0 = Verkauf.
    Gibt eine Series mit den steuerpflichtigen Gewinnen pro Verkauf zurück.
    """
    purchases = []  # Queue: (Datum, Investitionsbetrag, NAV zum Kauf)
    taxable_gains = pd.Series(0.0, index=df.index)

    for idx, row in df.iterrows():
        if "Cash_Flow" not in df.columns:
            continue
        cash_flow = row["Cash_Flow"]
        end_nav = row["End_NAV"]
        if cash_flow < 0:  # Kauf (Einzahlung vom Anleger ins Depot)
            purchases.append((row["Date"], -cash_flow, end_nav))
        elif cash_flow > 0:  # Verkauf (Ausschüttung an Anleger)
            sale_proceeds = float(cash_flow)
            remaining = sale_proceeds
            realized_gain = 0.0
            while remaining > 0 and purchases:
                p_date, p_amt, p_nav = purchases[0]
                take = min(p_amt, remaining)
                cost_basis = (p_nav / p_amt) * take if p_amt != 0 else 0.0
                realized_gain += take - cost_basis
                p_amt -= take
                remaining -= take
                if p_amt <= 0:
                    purchases.pop(0)
                else:
                    purchases[0] = (p_date, p_amt, p_nav)
            taxable_gains.iloc[idx] = max(0.0, realized_gain)
    return taxable_gains


def twr_simple_series(
    end_nav: pd.Series, dates: pd.Series, window: int, business_days: bool
) -> pd.Series:
    """
    Berechnet die einfache zeitgewichtete Rendite (TWR) für eine Serie von Depotwerten.

    Args:
        end_nav: Serie der Depotwerte.
        dates: Serie der zugehörigen Daten.
        window: Größe des rollierenden Fensters.
        business_days: Wenn True, werden nur Handelstage berücksichtigt.

    Returns:
        Serie der einfachen TWR-Renditen.
    """
    if business_days:
        shifted = end_nav.shift(window)
        return end_nav / shifted - 1.0
    else:
        s = end_nav.copy()
        s.index = pd.to_datetime(dates)
        base = s / s.shift(freq=pd.Timedelta(days=window))
        base = base.reindex(s.index)
        return base - 1.0


def twr_flow_adjusted_series(
    end_nav: pd.Series, cash_flow: pd.Series, dates: pd.Series, window: int, business_days: bool
) -> pd.Series:
    """
    Berechnet die flussbereinigte zeitgewichtete Rendite (TWR) für eine Serie von Depotwerten.

    Args:
        end_nav: Serie der Depotwerte.
        cash_flow: Serie der Cash-Flows.
        dates: Serie der zugehörigen Daten.
        window: Größe des rollierenden Fensters.
        business_days: Wenn True, werden nur Handelstage berücksichtigt.

    Returns:
        Serie der flussbereinigten TWR-Renditen.
    """
    cash = (
        (cash_flow if cash_flow is not None else pd.Series(0.0, index=end_nav.index))
        .fillna(0.0)
        .astype(float)
    )
    prev_nav = end_nav.shift(1)
    daily_r = (end_nav - cash) / prev_nav - 1.0
    daily_r.iloc[0] = np.nan
    if business_days:
        prod = (1.0 + daily_r).rolling(window=window, min_periods=window).apply(np.prod, raw=True)
        return prod - 1.0
    else:
        s = (1.0 + daily_r).copy()
        s.index = pd.to_datetime(dates)
        prod = s.rolling(window=f"{window}D", min_periods=1).apply(np.prod, raw=True)
        return prod.reindex(s.index) - 1.0


def rolling_time_weighted(
    df: pd.DataFrame,
    window: int,
    mode: TWRMode,
    business_days: bool,
    cash_override: Optional[pd.Series] = None,
) -> pd.Series:
    """
    Berechnet die rollierende zeitgewichtete Rendite (TWR) für einen DataFrame.

    Args:
        df: DataFrame mit Depotwerten und optional Cash-Flows.
        window: Größe des rollierenden Fensters.
        mode: Modus der Berechnung ('simple' oder 'flow-adjusted').
        business_days: Wenn True, werden nur Handelstage berücksichtigt.
        cash_override: Optionale Serie von Cash-Flows zur Überschreibung.

    Returns:
        Serie der TWR-Renditen.
    """
    end_nav = df["End_NAV"].astype(float)
    dates = df["Date"]
    cash = (
        cash_override
        if cash_override is not None
        else (df["Cash_Flow"] if "Cash_Flow" in df.columns else None)
    )
    if mode == "simple":
        return twr_simple_series(end_nav, dates, window, business_days)
    elif mode == "flow-adjusted":
        if cash is None:
            raise ValueError("Für 'flow-adjusted' ist eine Cash_Flow-Spalte erforderlich.")
        return twr_flow_adjusted_series(end_nav, cash.astype(float), dates, window, business_days)
    else:
        raise ValueError(f"Unbekannter TWR-Modus: {mode}")


def rolling_mwr_xirr(
    df: pd.DataFrame,
    window: int,
    business_days: bool,
    tax_rate: float = 0.0,
    tax_allowance: float = 0.0,
    include_tax: bool = False,
) -> pd.Series:
    """
    Berechnet die rollierende geldgewichtete Rendite (MWR) mithilfe von XIRR.

    Args:
        df: DataFrame mit Depotwerten und Cash-Flows.
        window: Größe des rollierenden Fensters.
        business_days: Wenn True, werden nur Handelstage berücksichtigt.
        tax_rate: Steuerrate für die Berechnung der Steuern.
        tax_allowance: Steuerfreibetrag.
        include_tax: Wenn True, werden Steuern in der Berechnung berücksichtigt.

    Returns:
        Serie der MWR-Renditen.
    """
    try:
        import numpy_financial as npf
    except ImportError as exc:
        raise RuntimeError(
            "numpy-financial ist erforderlich (pip install numpy-financial)."
        ) from exc

    irr_series = pd.Series(np.nan, index=df.index, dtype=float)
    taxable_gains = calculate_fifo_cost_basis(df) if include_tax else pd.Series(0.0, index=df.index)

    for idx in tqdm(range(len(df)), desc="Berechne geldgewichtete Rendite (XIRR)"):
        if business_days:
            # fmt: off
            window_df = df.iloc[max(0, idx - window + 1) : idx + 1]  # noqa: E203
            # fmt: on
        else:
            end_date = df.at[idx, "Date"]
            start_date = end_date - pd.Timedelta(days=window)
            mask = (df["Date"] > start_date) & (df["Date"] <= end_date)
            window_df = df.loc[mask]

        if "Cash_Flow" not in window_df.columns:
            continue

        cash = (-window_df["Cash_Flow"].astype(float)).tolist()
        if include_tax:
            window_gains = taxable_gains[window_df.index].sum()
            taxable_income = max(0, window_gains - tax_allowance)
            tax = taxable_income * tax_rate
            cash[-1] -= tax  # Steuer als Abfluss am Fensterende

        cash.append(float(window_df.iloc[-1]["End_NAV"]))
        cf_dates = window_df["Date"].tolist()

        try:
            irr_series.iloc[idx] = npf.xirr(cash, cf_dates)
        except Exception:
            irr_series.iloc[idx] = np.nan

    return irr_series


def _annualize(window_return: pd.Series, window: int) -> pd.Series:
    """Annualisiert Renditen: (1 + R)^(365/window) - 1.

    Args:
        returns: Serie mit Renditen (z. B. TWR oder MWR).
        window: Fenstergröße (Tage).

    Returns:
        pd.Series: Annualisierte Renditen.
    """
    with np.errstate(invalid="ignore"):
        return (1.0 + window_return) ** (365.0 / float(window)) - 1.0


def _as_path(p):
    if p is None:
        return None
    return p if isinstance(p, Path) else Path(p)


def run_legacy(
    *,
    csv_file: Path,
    nav_file: Path | None = None,
    flows_file: Path | None = None,
    csv_in_sep: str = ",",
    csv_in_decimal: str = ".",
    csv_out_sep: str = ",",
    csv_out_decimal: str = ".",
    twr_mode: TWRMode = "simple",
    window: int = 252,
    business_days: bool = False,
    annualize: bool = False,
    money_weighted: bool = False,
    tax_rate: float = 0.25,
    tax_allowance: float = 1000.0,
    church_tax: float = 0.09,
    soli: bool = False,
    include_tax: bool = False,
    output: Path | None = None,
    output_prefix: Path | None = None,
    plot: bool = False,
    plot_title: Optional[str] = None,
    save_svg: bool = False,
) -> Dict[str, Any]:
    """
    Berechnet rollierende Renditen für ein Portfolio, optional mit Steuer- und Gebührenanpassungen.

    Args:
        csv_file: Pfad zur kombinierten CSV-Datei.
        nav_file: Pfad zur NAV-Datei (optional).
        flows_file: Pfad zur Cash-Flow-Datei (optional).
        csv_in_sep: Trennzeichen für die Eingabe-CSV (Standard: ',').
        csv_in_decimal: Dezimalzeichen für die Eingabe-CSV (Standard: '.').
        csv_out_sep: Trennzeichen für die Ausgabe-CSV (Standard: ',').
        csv_out_decimal: Dezimalzeichen für die Ausgabe-CSV (Standard: '.').
        twr_mode: Modus für die TWR-Berechnung ('simple' oder 'flow-adjusted', Standard: 'simple').
        window: Größe des rollierenden Fensters (Standard: 252).
        business_days: Verwende Handelstage für das rollierende Fenster (Standard: False).
        annualize: Annualisiere die Renditen (Standard: False).
        money_weighted: Berechne geldgewichtete Renditen (Standard: False).
        plot: Erstelle einen Plot der Ergebnisse (Standard: False).
        plot_title: Titel für den Plot (optional).
        save_svg: Speichere den Plot als SVG (Standard: False).
        tax_rate: Basissteuersatz (Standard: 0.25).
        tax_allowance: Steuerfreibetrag (Standard: 1000.0).
        church_tax: Kirchensteuersatz (Standard: 0.09).
        soli: Berücksichtige Solidaritätszuschlag (Standard: False).
        include_tax: Berücksichtige Steuern in der Berechnung (Standard: False).
        output: Pfad zur Ausgabedatei (optional).
        output_prefix: Präfix für den Ausgabepfad (optional).

    Returns:
        Wörterbuch mit dem Ausgabepfad und dem DataFrame.
    """
    csv_file = _as_path(csv_file)
    nav_file = _as_path(nav_file)
    flows_file = _as_path(flows_file)
    output = _as_path(output)
    output_prefix = _as_path(output_prefix)
    # Steuerrate berechnen
    tax_rate = calculate_tax_rate(base_rate=tax_rate, soli=soli, church_tax=church_tax)

    # ---------- Input laden und zusammenführen ----------
    if not csv_file and not nav_file and not flows_file:
        raise SystemExit(
            "Bitte entweder --csv-file ODER (--nav-file und/oder --flows-file) angeben."
        )

    df = None
    if csv_file:
        df = read_csv_generic(csv_file, csv_in_sep, csv_in_decimal)  # NOTE: typo fixed below
    if nav_file:
        nav_df = read_csv_generic(nav_file, csv_in_sep, csv_in_decimal)
        if "End_NAV" not in nav_df.columns:
            raise ValueError("In --nav-file muss 'End_NAV' (oder Alias) vorhanden sein.")
        nav_df = nav_df[["Date", "End_NAV"]]
        nav_df = aggregate_by_date(nav_df)
        df = nav_df if df is None else pd.merge(df, nav_df, on="Date", how="outer")
    if flows_file:
        fl_df = read_csv_generic(flows_file, csv_in_sep, csv_in_decimal)
        if "Cash_Flow" not in fl_df.columns:
            raise ValueError("In --flows-file muss 'Cash_Flow' (oder Alias) vorhanden sein.")
        fl_df = fl_df[["Date", "Cash_Flow"]]
        fl_df = aggregate_by_date(fl_df)
        df = fl_df if df is None else pd.merge(df, fl_df, on="Date", how="outer")

    if df is None:
        raise SystemExit("Keine Daten geladen.")

    # Externe Gebühren vom Cash_Flow abziehen
    if "Fee_External" in df.columns:
        df["Cash_Flow"] = df["Cash_Flow"].fillna(0.0) - df["Fee_External"].fillna(0.0)

    # Validierung & Sortierung
    if "End_NAV" not in df.columns:
        raise ValueError("End_NAV fehlt in den Daten.")
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    df = aggregate_by_date(df)

    # Steuerpflichtige Gewinne berechnen (FIFO)
    if include_tax and "Cash_Flow" in df.columns:
        df["Taxable_Income"] = calculate_fifo_cost_basis(df)
    else:
        df["Taxable_Income"] = 0.0

    # Validierung
    if not pd.api.types.is_numeric_dtype(df["End_NAV"]):
        raise ValueError("Spalte 'End_NAV' muss numerisch sein.")
    if money_weighted and "Cash_Flow" not in df.columns:
        raise ValueError("Für --money-weighted wird 'Cash_Flow' benötigt.")
    if window <= 0:
        raise ValueError("Fenstergröße muss positiv sein.")
    if business_days and window >= len(df):
        logger.warning(
            f"Handelstage-Fenster ({window}) >= Anzahl Zeilen ({len(df)}). Verwende {len(df)-1}."
        )
        window = len(df) - 1

    # ---------- Berechnungen ----------
    df["Rolling_TWR"] = rolling_time_weighted(
        df, window=window, mode=twr_mode, business_days=business_days
    )

    if money_weighted:
        df["Rolling_MWR"] = rolling_mwr_xirr(
            df,
            window=window,
            business_days=business_days,
            tax_rate=tax_rate,
            tax_allowance=tax_allowance,
            include_tax=include_tax,
        )

    if business_days:
        win_taxable = df["Taxable_Income"].rolling(window=window, min_periods=window).sum()
    else:
        s_taxable = df["Taxable_Income"].copy()
        s_taxable.index = pd.to_datetime(df["Date"])
        win_taxable = s_taxable.rolling(window=f"{window}D").sum().reindex(s_taxable.index)
    df["Taxable_Income_Window"] = win_taxable
    df["Tax_Paid"] = (win_taxable - tax_allowance).clip(lower=0) * tax_rate

    if annualize:
        df["Rolling_TWR_Ann"] = _annualize(df["Rolling_TWR"], window)
        if money_weighted:
            df["Rolling_MWR_Ann"] = _annualize(df["Rolling_MWR"], window)

    out_path = output
    if out_path is None:
        base_name = "combined"
        parent_dir = Path.cwd()
        if csv_file:
            csv_file = Path(csv_file)
            base_name = csv_file.stem
            parent_dir = csv_file.parent
        elif nav_file:
            nav_file = Path(nav_file)
            base_name = nav_file.stem
            parent_dir = nav_file.parent
        elif flows_file:
            flows_file = Path(flows_file)
            base_name = flows_file.stem
            parent_dir = flows_file.parent

        # wenn output_prefix gesetzt -> dort, sonst im Ordner der Eingabedatei
        target_dir = Path(output_prefix) if output_prefix else parent_dir
        out_path = target_dir / f"{base_name}_with_returns.csv"

    cols = [
        "Date",
        "End_NAV",
        "Cash_Flow" if "Cash_Flow" in df.columns else None,
        "Fee_Internal" if "Fee_Internal" in df.columns else None,
        "Fee_External" if "Fee_External" in df.columns else None,
        "Tax_Internal" if "Tax_Internal" in df.columns else None,
        "Rolling_TWR",
        "Taxable_Income",
        "Tax_Paid",
        "Rolling_MWR" if money_weighted else None,
        "Rolling_TWR_Ann" if annualize else None,
        "Rolling_MWR_Ann" if money_weighted and annualize else None,
        "Taxable_Income_Window",
    ]
    cols = [c for c in cols if c is not None and c in df.columns]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = df[cols]
    df[cols].to_csv(
        out_path, index=False, float_format="%.6f", sep=csv_out_sep, decimal=csv_out_decimal
    )
    logger.info(f"Ergebnis gespeichert in: {out_path}")

    if plot:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Date"], df["Rolling_TWR"] * 100.0, label="TWR (netto)", linewidth=1.5)
        if money_weighted:
            plt.plot(
                df["Date"],
                df["Rolling_MWR"] * 100.0,
                label="MWR (XIRR)",
                linewidth=1.2,
                linestyle="--",
            )
        if include_tax:
            plt.plot(df["Date"], df["Tax_Paid"], label="Gezahlte Steuer (Fenster)", linewidth=1.0)
        plt.axhline(0, linewidth=0.8, linestyle=":")
        title = (
            plot_title
            or f"Rollierende {window}-{'Handels' if business_days else 'Kalender'}tage-Rendite"
        )
        if annualize:
            title += " (annualisiert)"
        plt.title(title)
        plt.xlabel("Datum")
        plt.ylabel("Rendite [%] / Steuer [€]")
        plt.legend()
        plt.grid(alpha=0.3)
        plot_png = out_path.with_suffix(".png")
        plt.tight_layout()
        plt.savefig(plot_png, dpi=300)
        if save_svg:
            plot_svg = out_path.with_suffix(".svg")
            plt.savefig(plot_svg)
        plt.close()
        logger.info(f"Plot gespeichert in: {plot_png}{' und ' + str(plot_svg) if save_svg else ''}")

    return {"out_path": out_path, "df": out}
