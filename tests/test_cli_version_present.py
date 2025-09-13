import rolling_returns as rr
import rolling_returns.cli as cli


def test_cli_version_prints_package_version(capsys):
    # Ensure __version__ exists
    assert hasattr(rr, "__version__")
    rc = cli.main_rr(["version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert rr.__version__ in out
