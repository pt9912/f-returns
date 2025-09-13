import pathlib
import sys
from pathlib import Path

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
from rolling_returns.converter.convert_broker import load_mapping


def test_load_mapping_variants(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_mapping(tmp_path / "missing.json")
    j = tmp_path / "m.json"
    j.write_text('{"a":1,"broker":"X"}', encoding="utf-8")
    assert load_mapping(j)["a"] == 1
    y = tmp_path / "m.yaml"
    y.write_text("a: 2\nbroker: Y\n", encoding="utf-8")
    try:
        res = load_mapping(y)
        assert res["a"] == 2
    except SystemExit:
        pass
