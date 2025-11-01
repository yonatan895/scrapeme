from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from core.serialization import dumps, to_jsonable


class Color(Enum):
    RED = "red"
    BLUE = "blue"


def _sample_payload() -> dict[str, Any]:
    return {
        "site": "example",
        "when": datetime(2025, 1, 1, 12, 0, 0),
        "path": Path("/tmp/file.txt"),
        "ok": True,
        "count": 3,
        "color": Color.RED,
        "items": [1, 2, {"p": Path("/x")}, [Color.BLUE, None]],
        "mapping": {1: "int_key", "s": 2},
    }


@pytest.mark.unit
def test_to_jsonable_minimal_adapters():
    obj = _sample_payload()
    j = to_jsonable(obj)
    # Ensure minimal conversions
    assert j["site"] == "example"
    assert isinstance(j["when"], str) and j["when"].startswith("2025-")
    assert j["path"] == "/tmp/file.txt"
    assert j["color"] == "red"
    assert j["items"][2]["p"] == "/x"
    # Non-str keys coerced
    assert j["mapping"]["1"] == "int_key"


@pytest.mark.unit
def test_dumps_fallback_and_bytes():
    j = to_jsonable(_sample_payload())
    data = dumps(j)
    assert isinstance(data, (bytes, bytearray))
    # stdlib fallback produces utf-8 encoded JSON; orjson also returns bytes
    parsed = json.loads(data.decode("utf-8"))
    assert parsed["site"] == "example"


@pytest.mark.unit
def test_jsonl_equivalence(tmp_path):
    rows = [to_jsonable({"i": i}) for i in range(3)]
    # Array form
    arr_bytes = dumps(rows)
    arr = [json.loads(x) for x in [arr_bytes.decode("utf-8")]][0]
    # JSONL form
    jsonl_path = tmp_path / "out.jsonl"
    with jsonl_path.open("wb") as fp:
        for r in rows:
            fp.write(dumps(r))
            fp.write(b"\n")
    jsonl_rows = [json.loads(line) for line in jsonl_path.read_text("utf-8").splitlines()]
    assert arr == jsonl_rows
