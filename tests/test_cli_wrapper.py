import importlib
import sys

import pytest

from rolling_returns.exceptions import DataLoadError, InvalidInputError, RollingReturnsError


def _reload_cli():
    if "rolling_returns.cli" in sys.modules:
        del sys.modules["rolling_returns.cli"]
    return importlib.import_module("rolling_returns.cli")


def test_cli_wrapper_success(capsys):
    cli = _reload_cli()
    # Erfolgsfall: wrapper soll Rückgabewert durchreichen, kein SystemExit
    result = cli._rr_exception_wrapper(lambda: 0)
    assert result == 0


def test_cli_wrapper_invalid_input(monkeypatch, capsys):
    cli = _reload_cli()

    def bad():
        raise InvalidInputError("bad arg")

    with pytest.raises(SystemExit) as ex:
        cli._rr_exception_wrapper(bad)
    assert ex.value.code == 2
    assert "Fehler: bad arg" in capsys.readouterr().err


def test_cli_wrapper_data_load(monkeypatch, capsys):
    cli = _reload_cli()

    def bad():
        raise DataLoadError("no data")

    with pytest.raises(SystemExit) as ex:
        cli._rr_exception_wrapper(bad)
    assert ex.value.code == 3


def test_cli_wrapper_generic(monkeypatch, capsys):
    cli = _reload_cli()

    def bad():
        raise RollingReturnsError("boom")

    with pytest.raises(SystemExit) as ex:
        cli._rr_exception_wrapper(bad)
    assert ex.value.code == 1
