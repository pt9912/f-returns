import types
from pathlib import Path

import pytest

import rolling_returns.converter.convert_broker as cb


def test_load_mapping_yaml_without_pyyaml(monkeypatch, tmp_path: Path):
    yml = tmp_path / "map.yml"
    yml.write_text("{}", encoding="utf-8")
    # simulate missing PyYAML
    monkeypatch.setattr(cb, "yaml", None)
    with pytest.raises(SystemExit):
        cb.load_mapping(yml)
