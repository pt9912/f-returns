import pytest

from rolling_returns.cli import main_rr


def test_cli_help_returns(monkeypatch):
    with pytest.raises(SystemExit) as ei:
        main_rr(["returns", "--help"])
    assert ei.value.code == 0 or ei.value.code == SystemExit.code


def test_cli_returns_missing_required(monkeypatch):
    with pytest.raises(SystemExit) as ei:
        main_rr(["returns"])
    assert ei.value.code != 0
