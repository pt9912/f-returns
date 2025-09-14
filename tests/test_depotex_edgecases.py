from pathlib import Path

import pytest

import rolling_returns.legacy.depotex as depotex
from rolling_returns.exceptions import DataLoadError


def test_run_legacy_raises_when_no_data_loaded(monkeypatch, tmp_path: Path):
    # Dummy-Datei (Inhalt wird durch Monkeypatch ignoriert)
    dummy = tmp_path / "dummy.csv"
    dummy.write_text("Date,End_NAV\n")

    # read_csv_generic so patchen, dass None zurückkommt -> triggert DataLoadError
    monkeypatch.setattr(depotex, "read_csv_generic", lambda *args, **kwargs: None)

    with pytest.raises(DataLoadError):
        depotex.run_legacy(
            csv_file=dummy,
            nav_file=None,
            flows_file=None,
            csv_in_sep=",",
            csv_in_decimal=".",
            csv_out_sep=",",
            csv_out_decimal=".",
            twr_mode="simple",
            window=3,
            business_days=False,
            annualize=False,
            money_weighted=False,
            tax_rate=0.25,
            tax_allowance=1000.0,
            church_tax=0.0,
            soli=False,
            include_tax=False,
            output=None,
            output_prefix=None,
            plot=False,
        )
