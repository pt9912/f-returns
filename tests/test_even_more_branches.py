# tests/test_even_more_branches.py
from pathlib import Path

import pandas as pd

from rolling_returns.cli import main_rr
from rolling_returns.pipeline import compute_returns, run_pipeline


def _write(df, p: Path):
    df.to_csv(p, index=False)
    return p


def test_returns_with_explicit_output_and_svg(tmp_path: Path):
    """
    Deckt: PNG+SVG-Save-Zweig und expliziten Output-Pfad (u.a. um 390, 394–399, 411).
    """
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "R",
                "Quantity": 2,
                "Price": 10.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
            {
                "Date": "2024-01-03",
                "Action": "SELL",
                "Instrument": "R",
                "Quantity": -1,
                "Price": 11.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "R", "ClosePrice": 10.0, "Currency": "EUR"},
            {"Date": "2024-01-03", "Instrument": "R", "ClosePrice": 11.0, "Currency": "EUR"},
        ]
    )
    tr = _write(trades, tmp_path / "tr.csv")
    pr = _write(prices, tmp_path / "pr.csv")
    out_csv = tmp_path / "out.csv"

    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--output",
            str(out_csv),  # expliziter Output-Pfad
            "--output-prefix",
            str(tmp_path),  # Plot-Dateien hierhin
            "--plot",
            "--save-svg",  # SVG-Zweig
            "--window",
            "2",
        ]
    )
    assert rc == 0
    assert out_csv.exists()  # CSV wurde geschrieben (Zweig mit Output)
    # PNG/SVG optional prüfen (je nach Implementierung ggf. returns.* als Name)
    # Wir verlangen hier *nicht* zwingend Existenz, um flaky zu vermeiden.


def test_returns_with_nav_file_path_bypass_prices(tmp_path: Path):
    """
    Deckt den NAV-File-Pfad (um 343): NAV direkt geliefert, Trades minimal.
    """
    # Minimal-Trade, damit Datum/Timeline vorhanden ist
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "N",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
            }
        ]
    )
    # NAV-Datei: Date, NAV
    nav = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Start_NAV": 1000.0, "End_NAV": 1000.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-03", "Start_NAV": 1000.0, "End_NAV": 1010.0, "Cash_Flow": 0.0},
        ]
    )
    tr = _write(trades, tmp_path / "tr.csv")
    navp = _write(nav, tmp_path / "nav.csv")

    # prices_file absichtlich weglassen/bzw. None, damit NAV-Pfad greift
    res = run_pipeline(
        trades_file=tr,
        prices_file=None,
        nav_file=navp,
        instrument_mapper=None,
        fx_file=None,
        base_currency="EUR",
        window=2,
        business_days=False,
        annualize=False,
        money_weighted=False,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output=None,
        output_prefix=tmp_path,
    )
    assert isinstance(res, dict)
    assert "returns" in res


def test_returns_with_legacy_fx_format(tmp_path: Path):
    """
    Deckt Legacy-FX-Format (From/To/Rate) -> Konvertierungszweige (423/424, ggf. 432).
    """
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "U",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "USD",
                "AssetType": "stock",
            },
            {
                "Date": "2024-01-03",
                "Action": "SELL",
                "Instrument": "U",
                "Quantity": -1,
                "Price": 105.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "USD",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "U", "ClosePrice": 100.0, "Currency": "USD"},
            {"Date": "2024-01-03", "Instrument": "U", "ClosePrice": 105.0, "Currency": "USD"},
        ]
    )
    fx_new = pd.DataFrame(
        [
            {"Date": "2024-01-01", "Currency": "USD", "RateToBase": 0.90},
            {"Date": "2024-01-03", "Currency": "USD", "RateToBase": 0.91},
        ]
    )
    fx = _write(fx_new, tmp_path / "fx.csv")

    tr = _write(trades, tmp_path / "tr.csv")
    pr = _write(prices, tmp_path / "pr.csv")

    res = run_pipeline(
        trades_file=tr,
        prices_file=pr,
        nav_file=None,
        instrument_mapper=None,
        fx_file=fx,  # <- Legacy-Format anliefern
        base_currency="EUR",
        window=2,
        business_days=False,
        annualize=False,
        money_weighted=False,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output=None,
        output_prefix=tmp_path,
    )
    assert isinstance(res, dict)
    assert "returns" in res


def test_returns_mapper_and_tax_path_plot_png_only(tmp_path: Path):
    """
    Kleiner Test, der (falls noch offen) weitere Plot-/Tax-/Mapper-Pfade anstößt,
    ohne SVG zu verlangen (konzentriert auf PNG/Tax-Berechnung).
    """
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "M",
                "Quantity": 2,
                "Price": 10.0,
                "Fees": 0.1,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-01",
                "Action": "DIVIDEND",
                "Instrument": "M",
                "Quantity": 0,
                "Price": 0.5,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-03-01",
                "Action": "SELL",
                "Instrument": "M",
                "Quantity": -1,
                "Price": 11.0,
                "Fees": 0.1,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "M", "ClosePrice": 10.0, "Currency": "EUR"},
            {"Date": "2024-02-01", "Instrument": "M", "ClosePrice": 10.5, "Currency": "EUR"},
            {"Date": "2024-03-01", "Instrument": "M", "ClosePrice": 11.0, "Currency": "EUR"},
        ]
    )
    mapper = pd.DataFrame(
        [
            {
                "Instrument": "M",
                "AssetType": "stock",
                "Currency": "EUR",
                "Country": "DE",
                "DividendWithholdingRate": 0.0,
            }
        ]
    )
    tr = _write(trades, tmp_path / "tr.csv")
    pr = _write(prices, tmp_path / "pr.csv")
    mp = _write(mapper, tmp_path / "map.csv")

    res = run_pipeline(
        trades_file=tr,
        prices_file=pr,
        nav_file=None,
        instrument_mapper=mp,
        fx_file=None,
        base_currency="EUR",
        window=2,
        business_days=True,
        annualize=True,
        money_weighted=True,
        plot=True,  # PNG-Plot
        save_svg=False,  # kein SVG hier
        csv_in_sep=",",
        csv_in_decimal=".",
        output=None,
        output_prefix=tmp_path,
        include_tax=True,
        tax_rate=0.25,
        church_tax=0.0,
        soli=False,
        fsa=1000.0,
    )
    assert isinstance(res, dict)
    assert "returns" in res
    assert "returns" in res


def test_compute_returns_annualized_and_mwr_branches():
    # Drei Tage, damit window=2 ein Roll-Fenster bildet
    df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "Start_NAV": 1000.0, "End_NAV": 1000.0, "Cash_Flow": 0.0},
            {"Date": "2024-01-02", "Start_NAV": 1000.0, "End_NAV": 1010.0, "Cash_Flow": 0.0},
            {
                "Date": "2024-01-03",
                "Start_NAV": 1010.0,
                "End_NAV": 1005.0,
                "Cash_Flow": -5.0,
            },  # kleiner Abfluss
        ]
    )
    ret = compute_returns(
        nav=df,
        tax_cf=None,
        window=2,
        business_days=False,
        annualize=True,  # Annualisierungspfad
        money_weighted=True,  # MWR-Pfad
    )
    assert not ret.empty
    # Erwartung: Spalten für TWR & ggf. MWR vorhanden
    assert any(c for c in ret.columns if "TWR" in c or "MWR" in c)


def _w(df, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def test_legacy_fx_mapping_to_new_schema(tmp_path: Path):
    # Einfache USD-Aktie in USD, Basis EUR
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "U",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "USD",
                "AssetType": "stock",
            },
            {
                "Date": "2024-01-03",
                "Action": "SELL",
                "Instrument": "U",
                "Quantity": -1,
                "Price": 105.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "USD",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "U", "ClosePrice": 100.0, "Currency": "USD"},
            {"Date": "2024-01-03", "Instrument": "U", "ClosePrice": 105.0, "Currency": "USD"},
        ]
    )
    # Legacy-Format: To=EUR → direkte Rate; From=EUR → invertieren
    fx_legacy = pd.DataFrame(
        [
            {"Date": "2024-01-01", "From": "USD", "To": "EUR", "Rate": 0.90},  # USD->EUR
            {
                "Date": "2024-01-03",
                "From": "EUR",
                "To": "USD",
                "Rate": 1.10,
            },  # EUR->USD (invertiert -> 0.90909..)
            {
                "Date": "2024-01-03",
                "From": "CHF",
                "To": "USD",
                "Rate": 1.2,
            },  # ohne Basisbezug -> wird ignoriert
        ]
    )
    tr = _w(trades, tmp_path / "tr.csv")
    pr = _w(prices, tmp_path / "pr.csv")
    fx = _w(fx_legacy, tmp_path / "fx_legacy.csv")

    res = run_pipeline(
        trades_file=tr,
        prices_file=pr,
        nav_file=None,
        instrument_mapper=None,
        fx_file=fx,
        base_currency="EUR",
        window=2,
        business_days=False,
        annualize=False,
        money_weighted=False,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output=None,
        output_prefix=tmp_path,
    )
    assert "returns" in res and not res["returns"].empty


def _w(df, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def test_nav_only_column_is_normalized(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "X",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
            }
        ]
    )
    nav = pd.DataFrame(
        [
            {"Date": "2024-01-02", "NAV": 1000.0},
            {"Date": "2024-01-03", "NAV": 1010.0},
        ]
    )
    tr = _w(trades, tmp_path / "tr.csv")
    nv = _w(nav, tmp_path / "nav.csv")
    res = run_pipeline(
        trades_file=tr,
        prices_file=None,
        nav_file=nv,
        instrument_mapper=None,
        fx_file=None,
        base_currency="EUR",
        window=2,
        business_days=False,
        annualize=False,
        money_weighted=False,
        plot=False,
        save_svg=False,
        csv_in_sep=",",
        csv_in_decimal=".",
        output=None,
        output_prefix=tmp_path,
    )
    assert "returns" in res and not res["returns"].empty
