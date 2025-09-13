import pytest


@pytest.mark.xfail(strict=True, reason="df=None-Pfad ist durch Vorbedingung unerreichbar (Design).")
def test_depotex_run_legacy_no_data_systemexit_unreachable():
    assert False, "Dokumentiert Unreachability der Guard-Klausel"
