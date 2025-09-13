import builtins
import importlib
import sys
from io import StringIO

import rolling_returns as rr
import rolling_returns.cli as cli


def test_cli_version_shows_unknown(monkeypatch, capsys):
    # Remove __version__ from package, forcing fallback branch
    if hasattr(rr, "__version__"):
        delattr(rr, "__version__")
    # Execute version subcommand
    rc = cli.main_rr(["version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Version: unknown" in out


def test_cli_no_args_prints_help_and_returns_1(capsys):
    rc = cli.main_rr([])
    out = capsys.readouterr().out
    assert rc == 1
    assert "usage:" in out.lower()
