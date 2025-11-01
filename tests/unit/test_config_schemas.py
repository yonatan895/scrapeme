import os
from pathlib import Path
from typing import Iterable

import pytest

from config.loader import load_sites


def _all_yaml_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.yaml"):
        yield p


@pytest.mark.unit
def test_all_yaml_configs_load(tmp_path: Path):
    """Ensure every YAML under config/ can be loaded by the loader without errors.

    This is a fast schema sanity check that prevents broken YAML or mismatched models
    from landing in the repo.
    """
    config_root = Path(__file__).resolve().parents[1] / ".." / "config"
    config_root = config_root.resolve()

    found = False
    for yaml_path in _all_yaml_files(config_root):
        found = True
        sites = load_sites(yaml_path)  # must not raise
        assert sites, f"No sites loaded from {yaml_path}"
        for site in sites:
            assert site.name and site.base_url
            assert site.wait_timeout_sec > 0
            assert site.page_load_timeout_sec > 0
    assert found, "No YAML config files found under config/"
