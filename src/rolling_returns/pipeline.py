"""
rolling_returns.py - Berechnung rollierender Renditen und Steuerberichte (v1.8.3).

Zwei Betriebsmodi:
1. **Legacy-Depot**: Ausgelagerte v1.6-Kompatibilität (über `legacy_mode.legacy_process`).
2. **Trades/Prices**: Moderne Pipeline mit Instrument-Mapper, FX-Handling
   und Dividenden-Quellensteuer.

Wichtige Funktionen:
- FIFO-Gewinnberechnung für Trades (inkl. FX-Umrechnung).
- Jährliche Verlustverrechnungstopfs (FSA, Kirchensteuer, Soli).
- NAV-Berechnung aus Trades und Preisen.
- Rollierende Renditen (TWR/MWR) mit Annualisierung.
- Steuerberichte (indikativ, keine Rechtsberatung!).

Abhängigkeiten:
- pandas, numpy, numpy_financial (für XIRR), matplotlib (für Plots).
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
TOPFS = ["stock", "fund", "bond", "derivative", "other"]


def fx_lookup(fx, dt, ccy, base):
    """Such den FX-Kurs für eine Währung zum gegebenen Datum.

    Args:
        fx: DataFrame mit FX-Daten (Spalten: Date, Currency, RateToBase).
        dt: Datum (pd.Timestamp oder kompatibel).
        ccy: Währung (str), z. B. "USD".
        base: Basiswährung (str), z. B. "EUR".

    Returns:
        float: FX-Kurs (1.0, falls nicht gefunden).
    """
    if fx is None or ccy == base or not isinstance(ccy, str) or ccy == "":
        return 1.0
    sub = fx[fx["Currency"] == ccy]
    if sub.empty:
        return 1.0
    sub = sub[sub["Date"] <= dt]
    if sub.empty:
        return float(fx[fx["Currency"] == ccy]["RateToBase"].iloc[0])
    return float(sub.iloc[-1]["RateToBase"])


def read_df(path, sep, dec):
    """Liest eine CSV-Datei als DataFrame.

    Args:
        path: Pfad zur CSV-Datei.
        sep: Trennzeichen.
        dec: Dezimaltrennzeichen.

    Returns:
        pd.DataFrame: Eingelesene Daten.
    """
    return pd.read_csv(path, sep=sep, decimal=dec)


def read_trades(path, sep, dec):
    """Liest Trades aus einer CSV-Datei.

    Args:
        path: Pfad zur Trades-CSV.
        sep: Trennzeichen.
        dec: Dezimaltrennzeichen.

    Returns:
        pd.DataFrame: Trades mit validierten Spalten.
    """
    df = read_df(path, sep, dec)
    req = ["Date", "Action", "Instrument", "Quantity", "Price", "Fees", "Tax"]
    for c in req:
        if c not in df.columns:
            raise ValueError(f"Spalte '{c}' fehlt in Trades: {path}")
    if "AssetType" not in df.columns:
        df["AssetType"] = "stock"
    if "Currency" not in df.columns:
        df["Currency"] = "EUR"
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    for c in ["Quantity", "Price", "Fees", "Tax"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["Action"] = df["Action"].str.upper().str.strip()
    df["AssetType"] = df["AssetType"].str.lower().str.strip()
    return df


def read_prices(path, sep, dec):
    """Liest Preise aus einer CSV-Datei.

    Args:
        path: Pfad zur Prices-CSV.
        sep: Trennzeichen.
        dec: Dezimaltrennzeichen.

    Returns:
        pd.DataFrame: Preise mit validierten Spalten.
    """
    df = read_df(path, sep, dec)
    for c in ["Date", "Instrument", "ClosePrice"]:
        if c not in df.columns:
            raise ValueError(f"Spalte '{c}' fehlt in Prices: {path}")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values(["Instrument", "Date"]).reset_index(drop=True)
    df["ClosePrice"] = pd.to_numeric(df["ClosePrice"], errors="coerce")
    return df


def read_fx(path, sep, dec):
    """Liest FX-Daten aus einer CSV-Datei.

    Args:
        path: Pfad zur FX-CSV.
        sep: Trennzeichen.
        dec: Dezimaltrennzeichen.

    Returns:
        pd.DataFrame: FX-Daten mit validierten Spalten.
    """
    # Fehlertolerant: Falls keine Datei vorhanden ist → leerer DF
    if path is None or not Path(path).exists():
        return pd.DataFrame(columns=["Date", "From", "To", "Rate"])
    fx = read_df(path, sep, dec)
    req = ["Date", "Currency", "RateToBase"]
    for c in req:
        if c not in fx.columns:
            raise ValueError(f"Spalte '{c}' fehlt in FX: {path}")
    fx["Date"] = pd.to_datetime(fx["Date"], errors="coerce")
    fx = fx.dropna(subset=["Date"]).sort_values(["Currency", "Date"]).reset_index(drop=True)
    fx["RateToBase"] = pd.to_numeric(fx["RateToBase"], errors="coerce")
    return fx


def apply_instrument_mapper(trades, mapper_path, sep, dec):
    """Wendet einen Instrument-Mapper auf Trades an.

    Args:
        trades: DataFrame mit Trades.
        mapper_path: Pfad zur Mapper-CSV.
        sep: Trennzeichen.
        dec: Dezimaltrennzeichen.

    Returns:
        pd.DataFrame: Mapper-Daten oder leerer DataFrame.
    """
    if mapper_path is None or not Path(mapper_path).exists():
        return pd.DataFrame()
    mp = read_df(mapper_path, sep, dec)
    if "Instrument" not in mp.columns:
        raise ValueError("Instrument-Mapper benötigt 'Instrument'")
    if "AssetType" in mp.columns:
        mp["AssetType"] = mp["AssetType"].str.lower().fillna("")
    if "Currency" in mp.columns:
        mp["Currency"] = mp["Currency"].fillna("")
    if "Country" in mp.columns:
        mp["Country"] = mp["Country"].fillna("")
    if "DividendWithholdingRate" in mp.columns:
        mp["DividendWithholdingRate"] = pd.to_numeric(
            mp["DividendWithholdingRate"], errors="coerce"
        ).fillna(0.0)
    t = trades.merge(mp, on="Instrument", how="left", suffixes=("", "_map"))
    trades["AssetType"] = (
        t.get("AssetType_map", trades.get("AssetType"))
        .combine_first(trades.get("AssetType"))
        .fillna("stock")
        .str.lower()
    )
    trades["Currency"] = (
        t.get("Currency_map", trades.get("Currency"))
        .combine_first(trades.get("Currency"))
        .fillna("EUR")
    )
    trades["Country"] = t.get("Country", pd.Series(index=trades.index, dtype=object)).fillna("")
    trades["DividendWithholdingRate"] = t.get(
        "DividendWithholdingRate", pd.Series(0.0, index=trades.index)
    ).fillna(0.0)
    return mp


def fifo_gains(trades, fx, base_ccy):
    """Berechnet FIFO-Gewinne/Verluste für Trades.

    Args:
        trades: DataFrame mit Trades.
        fx: DataFrame mit FX-Daten.
        base_ccy: Basiswährung (str).

    Returns:
        pd.DataFrame: Realisierte Gewinne pro Trade.
    """
    lots = {}
    recs = []
    for _, r in trades.iterrows():
        d, act, inst = r["Date"], r["Action"], r["Instrument"]
        qty, price, fees, tax = (
            float(r["Quantity"]),
            float(r["Price"]),
            float(r["Fees"]),
            float(r["Tax"]),
        )
        atype, ccy = r["AssetType"], r["Currency"]
        fxr = fx_lookup(fx, pd.Timestamp(d), ccy, base_ccy)
        lots.setdefault(inst, [])
        realized = 0.0
        if act == "BUY" and qty > 0:
            unit_cost = (qty * price * fxr + fees * fxr) / qty if qty else 0.0
            lots[inst].append([qty, unit_cost])
        elif act == "SELL" and qty > 0:
            proceeds = qty * price * fxr - fees * fxr
            rem = qty
            cost_total = 0.0
            while rem > 1e-12 and lots[inst]:
                lot_qty, u = lots[inst][0]
                take = min(lot_qty, rem)
                cost_total += take * u
                lot_qty -= take
                rem -= take
                if lot_qty <= 1e-12:
                    lots[inst].pop(0)
                else:
                    lots[inst][0][0] = lot_qty
            realized = proceeds - cost_total
        recs.append(
            dict(
                Date=d,
                Instrument=inst,
                Action=act,
                AssetType=atype,
                Currency=ccy,
                Quantity=qty,
                Price=price,
                Fees=fees,
                Tax=tax,
                FX=fxr,
                Realized_Gain_Base=realized,
            )
        )
    return pd.DataFrame.from_records(recs)


def yearly_loss_pots(twg, fsa, base_rate, church_tax, soli):
    """Berechnet jährliche Verlustverrechnungstopfs.

    Args:
        twg: DataFrame mit Trades und Gewinnen.
        fsa: Freibetrag (float).
        base_rate: Grundsteuersatz (float).
        church_tax: Kirchensteuersatz (float).
        soli: Solidaritätszuschlag (bool).

    Returns:
        pd.DataFrame: Jährliche Steuerberichte.
    """
    twg["Year"] = pd.to_datetime(twg["Date"]).dt.year
    years = sorted(twg["Year"].unique())
    carry = {t: 0.0 for t in TOPFS}
    rows = []
    eff = base_rate * (1.055 if soli else 1.0) * (1 + church_tax)
    for y in years:
        t = twg[(twg["Year"] == y) & (twg["Action"] == "SELL")]
        gains = {
            topf: float(t.loc[t["AssetType"] == topf, "Realized_Gain_Base"].sum()) for topf in TOPFS
        }
        after_loss = {}
        new_carry = {}
        for topf in TOPFS:
            win = max(0.0, gains[topf])
            loss = min(0.0, gains[topf])
            net = max(0.0, win + carry[topf])
            new_carry[topf] = min(0.0, win + carry[topf]) + loss
            after_loss[topf] = net
        taxable_before = sum(after_loss.values())
        fsa_used = min(fsa, taxable_before)
        taxable = max(0.0, taxable_before - fsa_used)
        tax_paid = taxable * eff
        rows.append(
            {
                "Year": y,
                **{f"Gain_{k}": gains[k] for k in TOPFS},
                **{f"NetAfterLoss_{k}": after_loss[k] for k in TOPFS},
                **{f"CarryEnd_{k}": new_carry[k] for k in TOPFS},
                "Taxable_Before_FSA": taxable_before,
                "FSA_Used": fsa_used,
                "Taxable_Income": taxable,
                "Tax_Paid": tax_paid,
                "Eff_Tax_Rate": eff,
            }
        )
        carry = new_carry
    return pd.DataFrame(rows)


def build_nav(trades, prices, fx, base_ccy):
    """Berechnet Net Asset Value (NAV) über die Zeit.

    Args:
        trades: DataFrame mit Trades.
        prices: DataFrame mit Preisen.
        fx: DataFrame mit FX-Daten.
        base_ccy: Basiswährung (str).

    Returns:
        pd.DataFrame: NAV pro Datum.
    """
    cal = pd.date_range(
        prices["Date"].min().normalize(), prices["Date"].max().normalize(), freq="D"
    )
    px = (
        prices.pivot_table(index="Date", columns="Instrument", values="ClosePrice")
        .sort_index()
        .reindex(cal)
        .ffill()
    )
    pos = {inst: 0.0 for inst in px.columns}
    cash = 0.0
    nav_rows = []
    by_date = trades.groupby(trades["Date"].dt.normalize())
    for dt, grp in by_date:
        if dt in by_date.groups:
            for _, r in grp.iterrows():
                act, inst = r["Action"], r["Instrument"]
                qty, price, fees, tax = (
                    float(r["Quantity"]),
                    float(r["Price"]),
                    float(r["Fees"]),
                    float(r["Tax"]),
                )
                ccy = r["Currency"]
                fxr = fx_lookup(fx, pd.Timestamp(dt), ccy, base_ccy)
                if act == "BUY":
                    pos[inst] = pos.get(inst, 0.0) + qty
                    cash -= (qty * price + fees) * fxr
                elif act == "SELL":
                    pos[inst] = pos.get(inst, 0.0) - qty
                    cash += (qty * price - fees) * fxr
                elif act == "DIV":
                    gross = qty * price if qty and price else 0.0
                    rate = r.get("DividendWithholdingRate", 0.0)
                    withheld = gross * rate
                    cash += (gross - withheld) * fxr
                    cash -= tax * fxr
                elif act == "FEE":
                    cash -= fees * fxr
                elif act == "TAX":
                    cash -= tax * fxr
        pv = 0.0
        if dt in px.index:
            row = px.loc[dt]
            for inst in px.columns:
                q = pos.get(inst, 0.0)
                pr = row.get(inst, float("nan"))
                if not pd.isna(pr) and abs(q) > 1e-12:
                    ccy_series = trades.loc[trades["Instrument"] == inst, "Currency"].dropna()
                    ccy = ccy_series.iloc[0] if not ccy_series.empty else base_ccy
                    fxr = fx_lookup(fx, pd.Timestamp(dt), ccy, base_ccy)
                    pv += q * pr * fxr
        nav_rows.append((dt, cash + pv))
    return pd.DataFrame(nav_rows, columns=["Date", "End_NAV"]).dropna()


def compute_returns(nav, tax_cf, window, business_days, annualize, money_weighted):
    """Berechnet rollierende Renditen (TWR/MWR).

    Args:
        nav: DataFrame mit NAV.
        tax_cf: DataFrame mit Steuer-Cashflows (optional).
        window: Rollierendes Fenster (int).
        business_days: Nur Handelstage (bool).
        annualize: Annualisierung (bool).
        money_weighted: MWR berechnen (bool).

    Returns:
        pd.DataFrame: Renditezeitreihen.
    """
    df = nav.copy().sort_values("Date").reset_index(drop=True)
    df["Cash_Flow"] = 0.0
    if tax_cf is not None and not tax_cf.empty:
        df = pd.merge(df, tax_cf, on="Date", how="left", suffixes=("", "_tax"))
        df["Cash_Flow"] = df["Cash_Flow"].fillna(0.0) + df["Cash_Flow_tax"].fillna(0.0)
        df = df.drop(columns=[c for c in df.columns if c.endswith("_tax")])
    end_nav = df["End_NAV"].astype(float)
    prev = end_nav.shift(1)
    daily_r = (end_nav - df["Cash_Flow"]) / prev - 1.0
    daily_r.iloc[0] = float("nan")
    if business_days:
        twr = (1.0 + daily_r).rolling(window=window, min_periods=window).apply(
            lambda x: x.prod(), raw=True
        ) - 1.0
    else:
        s = 1.0 + daily_r
        s.index = pd.to_datetime(df["Date"])
        twr = (
            s.rolling(window=f"{window}D").apply(lambda x: x.prod(), raw=True).reindex(s.index)
            - 1.0
        )
    df["Rolling_TWR"] = twr
    if money_weighted:
        try:
            import numpy_financial as npf

            irr = pd.Series(float("nan"), index=df.index)
            for i in range(len(df)):
                if business_days and i < window:
                    continue
                if business_days:
                    # fmt: off
                    w = df.iloc[max(0, i - window + 1):i + 1]  # noqa: E203
                    # fmt: on
                else:
                    end_date = df.at[i, "Date"]
                    start_date = end_date - pd.Timedelta(days=window)
                    w = df[(df["Date"] > start_date) & (df["Date"] <= end_date)]
                if w.empty:
                    continue
                cash = (-w["Cash_Flow"].astype(float)).tolist()
                cash.append(float(w.iloc[-1]["End_NAV"]))
                dates = w["Date"].tolist()
                try:
                    irr.iloc[i] = npf.xirr(cash, dates)
                except Exception:
                    irr.iloc[i] = float("nan")
            df["Rolling_MWR"] = irr
        except ImportError:
            logger.warning("numpy-financial fehlt – MWR entfällt.")
    if annualize:
        df["Rolling_TWR_Ann"] = (1.0 + df["Rolling_TWR"]) ** (365.0 / float(window)) - 1.0
        if "Rolling_MWR" in df.columns:
            df["Rolling_MWR_Ann"] = (1.0 + df["Rolling_MWR"]) ** (365.0 / float(window)) - 1.0
    return df


def run_pipeline(
    *,
    # Moduswahl
    trades_file: Path,
    prices_file: Path,
    nav_file: Path,
    # Dateien/Parser
    instrument_mapper: Optional[Path] = None,
    fx_file: Optional[Path] = None,
    csv_in_sep: str = ",",
    csv_in_decimal: str = ".",
    # Konfiguration
    base_currency: str = "EUR",
    window: int = 252,
    business_days: bool = False,
    annualize: bool = False,
    money_weighted: bool = False,
    plot: bool = False,
    save_svg: bool = False,
    # Steuern
    fsa: float = 1000.0,
    tax_rate: float = 0.25,
    church_tax: float = 0.09,
    soli: bool = False,
    include_tax: bool = False,
    # Ausgaben
    output: Optional[Path] = None,
    output_prefix: Path,
) -> Dict[str, Any]:
    """
    Haupt-Pipeline für den modernen Modus.

    Schritte:
    1. Lade und validiere Trades, Preise, FX.
    2. Wende Instrument-Mapper an.
    3. Berechne FIFO-Gewinne und Steuerberichte.
    4. Ermittle NAV (aus Preisen oder direkt aus `nav_file`).
    5. Berechne Renditen (TWR/MWR) und speichere Ergebnisse.
    6. Optional: Plotte Renditeverläufe.

    Returns:
        Dict[str, Any]: Enthält die Ergebnisse (`twg`, `yearly`, `nav`, `returns`, `out_dir`).
    """
    out_dir = Path(output or output_prefix or ".")
    out_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, Any] = {
        "twg": None,
        "yearly": None,
        "nav": None,
        "returns": None,
        "out_dir": out_dir,
    }

    trades = read_trades(trades_file, csv_in_sep, csv_in_decimal) if trades_file else None
    prices = read_prices(prices_file, csv_in_sep, csv_in_decimal) if prices_file else None
    fx = read_fx(fx_file, csv_in_sep, csv_in_decimal) if fx_file else None
    if trades is None:
        raise ValueError("trades_file wird benötigt (moderner Pfad).")

    _ = apply_instrument_mapper(trades, instrument_mapper, csv_in_sep, csv_in_decimal)

    twg = fifo_gains(trades, fx, base_currency)
    result["twg"] = twg
    yearly = yearly_loss_pots(twg, fsa, tax_rate, church_tax, soli)
    result["yearly"] = yearly

    # NAV
    if nav_file:
        nav = pd.read_csv(
            nav_file,
            sep=csv_in_sep,
            decimal=csv_in_decimal,
            parse_dates=["Date"],
        ).sort_values("Date")
    elif prices is not None:
        nav = build_nav(trades, prices, fx, base_currency)
        (out_dir / "nav.csv").write_text(nav.to_csv(index=False), encoding="utf-8")
    else:
        nav = None
    result["nav"] = nav

    # Ausgaben
    (out_dir / "trades_with_gains.csv").write_text(twg.to_csv(index=False), encoding="utf-8")
    (out_dir / "yearly_tax_report.csv").write_text(yearly.to_csv(index=False), encoding="utf-8")

    # Returns
    if nav is not None:
        tax_cf = None
        if include_tax and not yearly.empty:
            tax_cf = pd.DataFrame(
                {
                    "Date": pd.to_datetime([datetime(int(y), 12, 31) for y in yearly["Year"]]),
                    "Cash_Flow": -yearly["Tax_Paid"].astype(float).values,
                }
            )
        df_ret = compute_returns(nav, tax_cf, window, business_days, annualize, money_weighted)
        result["returns"] = df_ret
        (out_dir / "returns.csv").write_text(df_ret.to_csv(index=False), encoding="utf-8")
        if plot:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(12, 6))
            plt.plot(
                df_ret["Date"],
                df_ret["Rolling_TWR"] * 100.0,
                label="TWR (flow-adjusted)",
                linewidth=1.5,
            )
            if "Rolling_MWR" in df_ret.columns:
                plt.plot(
                    df_ret["Date"],
                    df_ret["Rolling_MWR"] * 100.0,
                    label="MWR (XIRR)",
                    linestyle="--",
                )
            plt.axhline(0, linewidth=0.8, linestyle=":")
            plt.grid(alpha=0.3)
            ttl = f"Rollierende {window}-{'Handels' if business_days else 'Kalender'}tage"
            if annualize:
                ttl += " (annualisiert)"
            plt.title(ttl)
            plt.xlabel("Datum")
            plt.ylabel("Rendite [%]")
            plt.legend()
            png = out_dir / "returns.png"
            plt.tight_layout()
            plt.savefig(png, dpi=200)
            plt.close()
            if save_svg:
                svg = out_dir / "returns.svg"
                plt.figure(figsize=(12, 6))
                plt.plot(
                    df_ret["Date"],
                    df_ret["Rolling_TWR"] * 100.0,
                    label="TWR (flow-adjusted)",
                    linewidth=1.5,
                )
                if "Rolling_MWR" in df_ret.columns:
                    plt.plot(
                        df_ret["Date"],
                        df_ret["Rolling_MWR"] * 100.0,
                        label="MWR (XIRR)",
                        linestyle="--",
                    )
                plt.axhline(0, linewidth=0.8, linestyle=":")
                plt.grid(alpha=0.3)
                plt.title(ttl)
                plt.xlabel("Datum")
                plt.ylabel("Rendite [%]")
                plt.legend()
                plt.tight_layout()
                plt.savefig(svg)
                plt.close()

    return result
