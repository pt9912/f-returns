import pytest

from rolling_returns.cli import main_rr


def test_cli_legacy_help():
    with pytest.raises(SystemExit) as ei:
        main_rr(["legacy", "--help"])
    assert ei.value.code == 0 or ei.value.code == SystemExit.code


def test_cli_legacy_missing_args():
    with pytest.raises(SystemExit) as ei:
        main_rr(["legacy"])
    assert ei.value.code != 0


def test_cli_legacyex_help():
    with pytest.raises(SystemExit) as ei:
        main_rr(["legacyex", "--help"])
    assert ei.value.code == 0 or ei.value.code == SystemExit.code


def test_cli_legacyex_missing_args():
    with pytest.raises(SystemExit) as ei:
        main_rr(["legacyex"])
    assert ei.value.code != 0
