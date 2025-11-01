from pathlib import Path

import pytest

from config.loader import load_sites


@pytest.mark.unit
def test_all_yaml_configs_load():
    config_root = Path(__file__).resolve().parents[2] / "config"
    assert config_root.exists(), "config/ directory not found"

    found_any = False
    for p in config_root.rglob("*.yaml"):
        found_any = True
        try:
            sites = load_sites(p)
        except Exception as e:  # keep test diagnostic, not to hide errors
            raise AssertionError(f"Failed to load {p}: {e}")
        assert sites is not None, f"Loader returned None for {p}"
    assert found_any, "No YAML files under config/"
