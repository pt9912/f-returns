## 2025-09-14 – Refactoring: `SystemExit` → typisierte Exceptions
- `rolling_returns.exceptions` mit `RollingReturnsError`, `DataLoadError`, `InvalidInputError` hinzugefügt.
- `SystemExit` in `legacy/depotex.py` durch typisierte Exceptions ersetzt (heuristische Abbildung).
- CLI bildet typisierte Exceptions nun auf Exit-Codes ab (2=InvalidInput, 3=DataLoad, 1=allgemeiner Fehler).
- Tests für Edge-Cases ergänzt (Leeres-Fenster-Prüfung, keine geladenen Daten).
