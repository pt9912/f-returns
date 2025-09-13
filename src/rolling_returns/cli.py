"""
f-returns CLI - Unified Command Line Interface für Renditeberechnungen.

Dieses Modul bietet eine einheitliche CLI für verschiedene Betriebsmodi:
- legacy: Verarbeitung von Legacy-Depot-CSVs (Single-CSV-Pfad)
- legacyex: Erweiterte Legacy-Verarbeitung (mit separaten NAV/Flows-Dateien)
- returns: Moderne Pipeline mit Trades/Prices + Mapper + FX
- convert: Konvertierung von Broker-spezifischen CSV-Dateien in standardisierte Formate
- version: Zeigt die Version des Pakets an

Jeder Subcommand hat eigene Argumente, die über die Hilfe angezeigt werden können.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .legacy.depot import run_legacy
from .legacy.depotex import run_legacy as run_legacy_ex
from .pipeline import run_pipeline


def _add_common_io_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--csv-in-sep", type=str, default=",")
    p.add_argument("--csv-in-decimal", type=str, default=".")
    p.add_argument("--csv-out-sep", type=str, default=",")
    p.add_argument("--csv-out-decimal", type=str, default=".")
    p.add_argument("--output", type=Path)
    p.add_argument("--output-prefix", type=Path, default=Path("."))


def _add_perf_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--window", type=int, default=252)
    p.add_argument("--business-days", action="store_true")
    p.add_argument("--annualize", action="store_true")
    p.add_argument("--money-weighted", action="store_true")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--save-svg", action="store_true")


def _add_tax_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--fsa", type=float, default=1000.0)
    p.add_argument("--tax-rate", type=float, default=0.25)
    p.add_argument("--church-tax", type=float, default=0.09)
    p.add_argument("--soli", action="store_true")
    p.add_argument("--include-tax", action="store_true")


def _legacy_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="f-returns legacy", description="Legacy (Single-CSV) Pfad")
    # vollständige Argumentliste (wie besprochen)
    p.add_argument("--csv-file", dest="csv_file", type=Path, required=True, help="Legacy Depot CSV")
    p.add_argument("--external-tax-column", type=str, default=None)
    p.add_argument("--nav-file", type=Path)
    p.add_argument("--instrument-mapper", type=Path)
    p.add_argument("--fx-file", type=Path)
    p.add_argument("--base-currency", dest="base_currency", type=str, default="EUR")
    _add_common_io_flags(p)
    _add_perf_flags(p)
    _add_tax_flags(p)
    ns = p.parse_args(argv)

    res = run_legacy(
        csv_file=ns.csv_file,
        external_tax_column=ns.external_tax_column,
        csv_in_sep=ns.csv_in_sep,
        csv_in_decimal=ns.csv_in_decimal,
        csv_out_sep=ns.csv_out_sep,
        csv_out_decimal=ns.csv_out_decimal,
        window=ns.window,
        business_days=ns.business_days,
        annualize=ns.annualize,
        money_weighted=ns.money_weighted,
        plot=ns.plot,
        save_svg=ns.save_svg,
        output=ns.output,
        output_prefix=ns.output_prefix,
    )
    if res.get("out_path"):
        print(f"Legacy-Ergebnis: {res['out_path']}")
    return 0


def _legacyex_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="f-returns legacy", description="Legacy (Single-CSV) Pfad")
    # vollständige Argumentliste (wie besprochen)
    p.add_argument("--csv-file", dest="csv_file", type=Path, required=True, help="Legacy Depot CSV")
    p.add_argument("--external-tax-column", type=str, default=None)
    p.add_argument("--nav-file", type=Path)
    p.add_argument("--flows-file", type=Path)
    p.add_argument("--instrument-mapper", type=Path)
    p.add_argument("--fx-file", type=Path)
    p.add_argument("--base-currency", dest="base_currency", type=str, default="EUR")
    _add_common_io_flags(p)
    _add_perf_flags(p)
    _add_tax_flags(p)
    ns = p.parse_args(argv)

    res = run_legacy_ex(
        csv_file=ns.csv_file,
        nav_file=ns.nav_file,
        flows_file=ns.flows_file,
        csv_in_sep=ns.csv_in_sep,
        csv_in_decimal=ns.csv_in_decimal,
        csv_out_sep=ns.csv_out_sep,
        csv_out_decimal=ns.csv_out_decimal,
        window=ns.window,
        business_days=ns.business_days,
        annualize=ns.annualize,
        money_weighted=ns.money_weighted,
        plot=ns.plot,
        save_svg=ns.save_svg,
        tax_rate=ns.tax_rate,
        church_tax=ns.church_tax,
        soli=ns.soli,
        include_tax=ns.include_tax,
        output=ns.output,
        output_prefix=ns.output_prefix,
    )
    if res.get("out_path"):
        print(f"Legacy-Ergebnis: {res['out_path']}")
    return 0


def _returns_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="f-returns returns", description="Moderne Pipeline (Trades/Prices + Mapper + FX)"
    )
    p.add_argument("--trades-file", dest="trades_file", type=Path, required=True)
    p.add_argument("--prices-file", dest="prices_file", type=Path)
    p.add_argument("--nav-file", type=Path)
    p.add_argument("--instrument-mapper", dest="instrument_mapper", type=Path)
    p.add_argument("--fx-file", dest="fx_file", type=Path)
    p.add_argument("--base-currency", dest="base_currency", type=str, default="EUR")
    _add_common_io_flags(p)
    _add_perf_flags(p)
    _add_tax_flags(p)
    ns = p.parse_args(argv)

    res = run_pipeline(
        trades_file=ns.trades_file,
        prices_file=ns.prices_file,
        nav_file=ns.nav_file,
        instrument_mapper=ns.instrument_mapper,
        fx_file=ns.fx_file,
        base_currency=ns.base_currency,
        csv_in_sep=ns.csv_in_sep,
        csv_in_decimal=ns.csv_in_decimal,
        window=ns.window,
        business_days=ns.business_days,
        annualize=ns.annualize,
        money_weighted=ns.money_weighted,
        plot=ns.plot,
        save_svg=ns.save_svg,
        fsa=ns.fsa,
        tax_rate=ns.tax_rate,
        church_tax=ns.church_tax,
        soli=ns.soli,
        include_tax=ns.include_tax,
        output=ns.output,
        output_prefix=ns.output_prefix,
    )
    if res.get("returns"):
        print(f"Ergebnis: {res['returns']}")
    return 0


def _convert_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        prog="f-returns convert",
        description="Broker-Konverter → trades.csv / prices.csv via Mapping",
    )
    sub = p.add_subparsers(dest="converter", required=True)
    g = sub.add_parser("generic", help="Generic broker CSV -> trades/prices")
    g.add_argument("--broker-trades", type=Path, help="Broker Trades CSV")
    g.add_argument("--broker-prices", type=Path, help="Broker Prices CSV")
    g.add_argument("--map-trades", type=Path, help="Mapping-Datei (YAML/JSON) für Trades")
    g.add_argument("--map-prices", type=Path, help="Mapping-Datei (YAML/JSON) für Prices")
    g.add_argument("--out-trades", type=Path, default=Path("trades.csv"))
    g.add_argument("--out-prices", type=Path, default=Path("prices.csv"))
    g.add_argument("--sep", type=str, default=",")
    g.add_argument("--decimal", type=str, default=".")
    ns = p.parse_args(argv)
    if ns.converter == "generic":
        from .converter.convert_broker import main as generic_main

        args = ["--input", ns.input, "--out", ns.out]
        if ns.dialect:
            args += ["--dialect", ns.dialect]
        if ns.config:
            args += ["--config", ns.config]
        return generic_main(ns)
    return 0


def main_rr(argv=None):
    """
    Haupt-Einstiegspunkt für die f-returns CLI.

    Parsed die Kommandozeilenargumente und leitet an den entsprechenden Subcommand weiter.

    Args:
        argv: Kommandozeilenargumente (Standard: sys.argv[1:])

    Returns:
        int: Rückgabewert (0 = Erfolg, 1 = Fehler)
    """
    argv = list(sys.argv[1:] if argv is None else argv)

    # Haupt-Parser für die CLI
    p = argparse.ArgumentParser(
        prog="f-returns",
        description="Unified CLI für Renditeberechnungen (legacy | legacyex | returns | convert | version)",
    )

    # Subparser für die verschiedenen Modi
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("legacy")
    sub.add_parser("legacyex")
    sub.add_parser("returns")
    sub.add_parser("convert")
    sub.add_parser("version")
    # Bei unbekannten Commands oder fehlenden Argumenten wird die Hilfe angezeigt
    if not argv:
        p.print_help()
        return 1
    cmd, rest = argv[0], argv[1:]
    if cmd == "legacy":
        return _legacy_main(rest)
    if cmd == "legacyex":
        return _legacyex_main(rest)
    if cmd == "returns":
        return _returns_main(rest)
    if cmd == "convert":
        return _convert_main(rest)
    if cmd == "version":
        # Versucht, die Version aus dem Paket zu lesen, fällt aber auf "unknown" zurück
        try:
            from . import __version__

            print(f"f-returns Version: {__version__}")
        except Exception:
            print("Version: unknown")
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main_rr())
