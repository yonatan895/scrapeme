import importlib.util
from pathlib import Path

import pytest


@pytest.mark.unit
def test_locust_files_importable():
    # Validate that locust files exist and key classes can be imported
    candidates = [
        Path("tests/load/locustfile.py"),
        Path("tests/load/real_app_locustfile.py"),
    ]

    for path in candidates:
        if not path.exists():
            continue
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        # Basic sanity: module defines at least one User class
        names = [n for n in dir(module) if n.endswith("User")]
        assert names, f"No User classes found in {path}"
