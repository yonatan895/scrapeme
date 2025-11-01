from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from core.serialization import dumps, to_jsonable


def make_result(i: int) -> dict[str, Any]:
    return {
        "site": f"site_{i}",
        "data": {
            "ts": datetime(2025, 1, 1, 12, 0, 0),
            "path": Path(f"/tmp/file_{i}.txt"),
            "ok": True,
            "count": i,
            "items": [i, i + 1, {"p": Path(f"/x/{i}")}],
            "map": {i: "v", "s": i},
        },
    }


@pytest.fixture(scope="session")
def results_normalized():
    rows = [to_jsonable(make_result(i)) for i in range(200)]
    return rows


@pytest.mark.benchmark(group="serialization")
def test_serialization_compact_array(benchmark, results_normalized):
    def _bench():
        return dumps(results_normalized)

    data = benchmark(_bench)
    parsed = json.loads(data.decode("utf-8"))
    assert isinstance(parsed, list)
    assert parsed and parsed[0]["site"].startswith("site_")


@pytest.mark.benchmark(group="serialization")
def test_serialization_jsonl(benchmark, results_normalized, tmp_path):
    def _bench():
        out = bytearray()
        for row in results_normalized:
            out += dumps(row) + b"\n"
        return bytes(out)

    data = benchmark(_bench)
    first = data.splitlines()[0]
    parsed = json.loads(first.decode("utf-8"))
    assert "site" in parsed


def test_orjson_in_use():
    # Ensure fast path available; pyproject pins orjson as required
    try:
        import orjson  # noqa: F401
    except Exception as e:  # pragma: no cover
        pytest.skip(f"orjson not importable: {e}")
    b = dumps({"a": 1})
    assert isinstance(b, (bytes, bytearray))
