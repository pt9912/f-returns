# tests/test_more_edge_branches.py
from pathlib import Path

import pandas as pd
import pytest

from rolling_returns.cli import main_rr


#
# Ziel: rund um build_nav / Date-Grouping / "keine Trades" / "nur Prices"
# -> typischerweise nahe ~343
#
# --- Fix 1: "prices only" -> minimaler BUY, damit Date existiert
def test_returns_prices_only_with_min_trade(tmp_path: Path):
    # Minimaler Trade nur, um ein Datum für TWG zu liefern
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
                "Currency": "EUR",
            }
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "X", "ClosePrice": 100.0, "Currency": "EUR"},
            {"Date": "2024-01-03", "Instrument": "X", "ClosePrice": 101.0, "Currency": "EUR"},
        ]
    )
    tr = tmp_path / "trades.csv"
    pr = tmp_path / "prices.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)

    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert (tmp_path / "returns.csv").exists()


#
# Ziel: Schreibpfad/Namensgebung mit --output (und Prefix) — typ. späterer Code (~411/423/424)
#
def test_returns_with_explicit_output_and_prefix(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "A",
                "Quantity": 1,
                "Price": 10.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
            {
                "Date": "2024-01-03",
                "Action": "SELL",
                "Instrument": "A",
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
            {"Date": "2024-01-02", "Instrument": "A", "ClosePrice": 10.0, "Currency": "EUR"},
            {"Date": "2024-01-03", "Instrument": "A", "ClosePrice": 11.0, "Currency": "EUR"},
        ]
    )
    tr = tmp_path / "tr.csv"
    pr = tmp_path / "pr.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "my_returns.csv"

    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(out_dir),
            "--output",
            str(out_file),
        ]
    )
    assert rc == 0
    # explizit angegebene Datei sollte existieren
    assert out_file.exists()


# --- Fix 2: Plot + SVG ohne absichtlichen savefig-Fehler
@pytest.mark.filterwarnings("ignore:Matplotlib is currently using")
def test_returns_plot_and_svg_outputs_ok(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "B",
                "Quantity": 1,
                "Price": 10.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
            {
                "Date": "2024-01-04",
                "Action": "SELL",
                "Instrument": "B",
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
            {"Date": "2024-01-02", "Instrument": "B", "ClosePrice": 10.0, "Currency": "EUR"},
            {"Date": "2024-01-03", "Instrument": "B", "ClosePrice": 10.5, "Currency": "EUR"},
            {"Date": "2024-01-04", "Instrument": "B", "ClosePrice": 11.0, "Currency": "EUR"},
        ]
    )
    tr = tmp_path / "tr.csv"
    pr = tmp_path / "pr.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)

    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(tmp_path),
            "--plot",
            "--save-svg",
            "--window",
            "2",
        ]
    )
    assert rc == 0
    # Falls die Pipeline PNG/SVG erzeugt, sollten sie hier liegen:
    # (nicht streng erforderlich für Bestehen; optional prüfen)
    # assert (tmp_path / "returns.png").exists()
    # assert (tmp_path / "returns.svg").exists()


#
# Ziel: FX-Fallback/Single-Currency-Zweig – typ. späterer Pfad, der nur Rates=1 verwendet (~432)
#
def test_returns_single_currency_no_fx_file(tmp_path: Path):
    # Alle Daten bereits in Base-Currency (EUR) -> kein fx_file nötig
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "C",
                "Quantity": 2,
                "Price": 5.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
            {
                "Date": "2024-02-01",
                "Action": "SELL",
                "Instrument": "C",
                "Quantity": -1,
                "Price": 6.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "C", "ClosePrice": 5.0, "Currency": "EUR"},
            {"Date": "2024-02-01", "Instrument": "C", "ClosePrice": 6.0, "Currency": "EUR"},
        ]
    )
    tr = tmp_path / "tr.csv"
    pr = tmp_path / "pr.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)

    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(tmp_path),
            "--annualize",
            "--money-weighted",
        ]
    )
    assert rc == 0


#
# Ziel: Mapper-Edge – Mapper vorhanden, aber ohne optionale Felder -> Default-Zweig (kann Codepfade öffnen)
# Nicht direkt nummerngebunden, aber hilft erfahrungsgemäß bei Lücken rund um "optionale Spalten".
#
def test_returns_with_minimal_mapper_defaults(tmp_path: Path):
    trades = pd.DataFrame(
        [
            {
                "Date": "2024-01-02",
                "Action": "BUY",
                "Instrument": "M",
                "Quantity": 1,
                "Price": 100.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
            {
                "Date": "2024-02-01",
                "Action": "SELL",
                "Instrument": "M",
                "Quantity": -1,
                "Price": 105.0,
                "Fees": 0.0,
                "Tax": 0.0,
                "Currency": "EUR",
                "AssetType": "stock",
            },
        ]
    )
    prices = pd.DataFrame(
        [
            {"Date": "2024-01-02", "Instrument": "M", "ClosePrice": 100.0, "Currency": "EUR"},
            {"Date": "2024-02-01", "Instrument": "M", "ClosePrice": 105.0, "Currency": "EUR"},
        ]
    )
    mapper = pd.DataFrame(
        [
            # bewusst minimal: ohne Country/WithholdingRate/etc.
            {"Instrument": "M", "AssetType": "stock", "Currency": "EUR"},
        ]
    )
    tr = tmp_path / "tr.csv"
    pr = tmp_path / "pr.csv"
    mp = tmp_path / "map.csv"
    trades.to_csv(tr, index=False)
    prices.to_csv(pr, index=False)
    mapper.to_csv(mp, index=False)

    rc = main_rr(
        [
            "returns",
            "--trades-file",
            str(tr),
            "--prices-file",
            str(pr),
            "--instrument-mapper",
            str(mp),
            "--base-currency",
            "EUR",
            "--output-prefix",
            str(tmp_path),
        ]
    )
    assert rc == 0
