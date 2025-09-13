#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_broker.py - Einheitliches CLI für Broker-Konvertierungen.

Dieses Modul konvertiert Broker-spezifische CSV-Dateien in standardisierte Formate.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import yaml

from .generic import convert_prices_df, convert_trades_df


def load_mapping(path: Optional[Path]) -> Dict[str, Any]:
    """Lädt eine Mapping-Datei (YAML oder JSON).

    Args:
        path: Pfad zur Mapping-Datei. Falls None, wird ein leeres Dict zurückgegeben.

    Returns:
        Dict[str, Any]: Geladenes Mapping.

    Raises:
        SystemExit: Falls PyYAML fehlt und eine YAML-Datei geladen werden soll.
    """
    if path is None:
        return {}

    if path.suffix.lower() in [".yml", ".yaml"]:
        if yaml is None:
            raise SystemExit("PyYAML nicht installiert. `pip install pyyaml` oder JSON verwenden.")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    return json.loads(path.read_text(encoding="utf-8"))


def main(ns: argparse.Namespace) -> int:
    """
    Hauptfunktion für die Broker-Konvertierung.

    Verarbeitet Trades und/oder Preise basierend auf den CLI-Argumenten.

    Args:
        ns: ArgumentParser-Namespace mit den CLI-Parametern:
            - broker_trades: Pfad zur Broker-spezifischen Trades-CSV (optional).
            - broker_prices: Pfad zur Broker-spezifischen Prices-CSV (optional).
            - map_trades: Pfad zur Mapping-Datei für Trades (optional).
            - map_prices: Pfad zur Mapping-Datei für Preise (optional).
            - out_trades: Ausgabepfad für konvertierte Trades (optional).
            - out_prices: Ausgabepfad für konvertierte Preise (optional).
            - sep: Trennzeichen für CSV-Dateien (Standard: ',').
            - decimal: Dezimaltrennzeichen für CSV-Dateien (Standard: '.').

    Returns:
        int: Rückgabewert für das CLI (0 = Erfolg).

    Workflow:
        1. Falls `broker_trades` angegeben: Lade Trades, wende Mapping an, speichere Ergebnis.
        2. Falls `broker_prices` angegeben: Lade Preise, wende Mapping an, speichere Ergebnis.
    """
    if ns.broker_trades:
        df = pd.read_csv(ns.broker_trades, sep=ns.sep, decimal=ns.decimal)
        mapping = load_mapping(ns.map_trades)
        out = convert_trades_df(df, mapping)
        out.to_csv(ns.out_trades, index=False)
        print(f"Wrote trades: {ns.out_trades}")

    if ns.broker_prices:
        df = pd.read_csv(ns.broker_prices, sep=ns.sep, decimal=ns.decimal)
        mapping = load_mapping(ns.map_prices)
        out = convert_prices_df(df, mapping)
        out.to_csv(ns.out_prices, index=False)
        print(f"Wrote prices: {ns.out_prices}")
    return 0
