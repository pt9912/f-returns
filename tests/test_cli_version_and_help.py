import builtins
from importlib import reload
from types import ModuleType

import pytest

import rolling_returns.cli as cli


def test_cli_help_top_level(capsys):
    rc = cli.main_rr(["--help"])
    out = capsys.readouterr().out
    assert rc == 0 or rc == 1  # help may return 0 or show then 1 to indicate no subcommand
    assert "legacy" in out and "convert" in out


def test_cli_version_subcommand(capsys):
    # Version subcommand should print either actual version or "unknown"
    rc = cli.main_rr(["version"])
    out = capsys.readouterr().out.lower()
    assert rc == 0
    assert "version" in out


def test_cli_unknown_subcommand_shows_help(capsys):
    rc = cli.main_rr(["does-not-exist"])
    out = capsys.readouterr().out.lower()
    assert rc == 1
    assert "usage" in out or "help" in out
