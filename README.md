# f-returns
**f-returns** ist ein Python-Toolkit zur Berechnung von **Rolling Returns**, steuerlicher Gewinnermittlung (FIFO, Verlusttöpfe) und FX-Umrechnung mit YAML-Broker-Profilen.
Es bietet CLI-Tools für Konvertierung, Analyse und Reporting von Handelsdaten – inkl. automatisierter Tests und CI/CD-Workflows.

---
## Features
- 📊 **Rolling Returns**: TWR (zeitgewichtet), MWR/XIRR (geldgewichtet), annualisiert
- 💰 **Steuerberechnung**: FIFO-Besteuerung, Verlustverrechnungstopfs (DE-spezifisch), Freistellungsauftrag
- 💱 **FX-Handling**: Umrechnung in Basiswährung (EUR/USD), historische Kurse
- 🏦 **Broker-Profile**: Konfigurierbar via YAML (Degiro, Trade Republic, Interactive Brokers, …)
- 🖥️ **CLI-Tools**:
  - `rolling-returns` (Haupttool für Renditeberechnungen)
  - `rr-convert` (Broker-CSV → standardisierte Formate)
- ✅ **Tests**: Unit-Tests + Property-Based Testing (Hypothesis)
- 🔄 **CI/CD**: Pre-commit, GitHub Actions, Release-Drafter

---
## Installation
```bash
# Environment einrichten
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Paket installieren (editable + Dev-Abhängigkeiten)
pip install -e ".[dev]"
pre-commit install
```

---
## CLI-Tools
### 1. Rolling Returns berechnen (moderner Pfad)
```bash
python -m rolling_returns returns \
  --trades-file data/trades.csv \
  --prices-file data/prices.csv \
  --out-dir out/ \
  --window 252 \
  --annualize
```

### 2. Broker-CSV konvertieren
```bash
python -m rolling_returns convert generic \
  --broker-trades data/raw/broker_trades.csv \
  --map-trades config/degiro_mapper.yaml \
  --out-trades data/trades.csv \
  --out-prices data/prices.csv
```

### 3. Legacy-Modus (Single-CSV)
```bash
python -m rolling_returns legacy \
  --csv-file data/depot.csv \
  --output out/depot_returns.csv \
  --plot
```

---
## Datenstruktur
Beispiel-Daten findest du in [`data/`](data/):

| Datei               | Spalten (Beispiel)                                                                 |
|---------------------|------------------------------------------------------------------------------------|
| [`trades.csv`](data/trades.csv) | `Date`, `Action`, `Instrument`, `Quantity`, `Price`, `Fees`, `Tax`, `Currency`     |
| [`prices.csv`](data/prices.csv) | `Date`, `Instrument`, `ClosePrice`                                                 |
| [`fx.csv`](data/fx.csv)       | `Date`, `Currency`, `RateToBase`                                                   |
| [`mapper.yaml`](config/)     | Broker-spezifische Spalten-Mappings (siehe [`config/degiro_mapper.yaml`](config/)) |

---
## Konfiguration
### Broker-Profile (YAML)
```yaml
# config/degiro_mapper.yaml
trades:
  Date: "broker_date"
  Instrument: "broker_isin"
  Quantity: "broker_quantity"
  Price: "broker_price"
  Fees: "broker_fees"
  Tax: "broker_tax"
  AssetType: "broker_product_type"  # Optional: "stock", "fund", etc.
  DividendWithholdingRate: 0.15     # Quellensteuer für Dividenden (z. B. 15% für US-Aktien)

prices:
  Date: "broker_date"
  Instrument: "broker_isin"
  ClosePrice: "broker_close_price"
```

---
## Entwicklung
```bash
# Linting & Formatting
pre-commit run --all-files

# Tests ausführen
pytest
pytest -q --cov=src --cov-report=term --cov-report=xml

# Paket bauen & veröffentlichen
python -m build
twine upload dist/*

# docker build
docker build -t f-returns:latest .

# tests
docker build --target tester -t f-returns:test .

# run
docker run --rm -v "$PWD:/work" -w /work f-returns:latest \
  legacyex --csv-file tests/data/sample.csv --output results.csv

```

> **Hinweis**:
> - Release Notes werden automatisch via [Release Drafter](.github/release-drafter.yml) generiert.
> - Für neue Broker-Profile: Mapping-YAML in `config/` hinzufügen und PR erstellen.

---
## Projektstatus
- **Version**: [![PyPI](https://img.shields.io/pypi/v/f-returns)](https://pypi.org/project/f-returns/)
- **Tests**: [![CI](https://github.com/pt9912/f-returns/actions/workflows/test.yml/badge.svg)](https://github.com/pt9912/f-returns/actions)
- **Coverage**: [![Coverage](https://coveralls.io/repos/github/pt9912/f-returns/badge.svg)](https://coveralls.io/github/pt9912/f-returns)
- **License**: MIT

---
## Beitragende
Pull Requests sind willkommen!
Für größere Änderungen bitte erst ein **Issue** erstellen, um die Design-Entscheidungen zu besprechen.

---
## Beispiel-Workflows
### 1. Degiro-Daten konvertieren → Renditen berechnen
```bash
# Schritt 1: Rohdaten konvertieren
python -m rolling_returns convert generic \
  --broker-trades data/raw/degiro_trades.csv \
  --map-trades config/degiro_mapper.yaml \
  --out-trades data/trades.csv

# Schritt 2: Renditen berechnen
python -m rolling_returns returns \
  --trades-file data/trades.csv \
  --prices-file data/prices.csv \
  --out-dir results/ \
  --money-weighted \
  --plot
```

### 2. Legacy-Depot analysieren
```bash
python -m rolling_returns legacy \
  --csv-file data/legacy_depot.csv \
  --output results/depot.csv \
  --tax-rate 0.26375  # inkl. Soli (25% + 5.5%)
```
