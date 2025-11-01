"""Serialization helpers for stable JSON encoding/decoding with strict types."""

from __future__ import annotations

from typing import Any

try:
    import orjson as _orjson
    HAS_ORJSON = True
except Exception:  # pragma: no cover - fallback path
    _orjson = None  # type: ignore[assignment]
    HAS_ORJSON = False
import json as _stdlib_json


def dumps_bytes(data: Any) -> bytes:
    """Serialize to JSON bytes.

    Uses orjson when available (returns bytes). Falls back to stdlib json
    and encodes to UTF-8 bytes.
    """
    if HAS_ORJSON and _orjson is not None:
        return _orjson.dumps(data)
    return _stdlib_json.dumps(data).encode("utf-8")


def dumps_str(data: Any) -> str:
    """Serialize to a JSON string (text)."""
    if HAS_ORJSON and _orjson is not None:
        return _orjson.dumps(data).decode("utf-8")
    return _stdlib_json.dumps(data)


def pretty_dumps(data: Any) -> str:
    """Pretty JSON string for logs and artifacts."""
    if HAS_ORJSON and _orjson is not None:
        indent_opt = getattr(_orjson, "OPT_INDENT_2", 0)
        return _orjson.dumps(data, option=indent_opt).decode("utf-8")
    return _stdlib_json.dumps(data, indent=2)


def loads(data: bytes | str) -> Any:
    """Deserialize JSON from bytes or string."""
    if isinstance(data, (bytes, bytearray)):
        if HAS_ORJSON and _orjson is not None:
            return _orjson.loads(data)
        return _stdlib_json.loads(data.decode("utf-8"))
    if HAS_ORJSON and _orjson is not None:
        return _orjson.loads(data)
    return _stdlib_json.loads(data)


# --- Backward-compatibility shims for tests ---

def dumps(data: Any, *, pretty: bool = False) -> bytes:
    """Compatibility wrapper returning bytes, matching old API.

    - pretty=False: compact bytes (fast)
    - pretty=True: pretty-printed bytes (UTF-8)
    """
    if pretty:
        return pretty_dumps(data).encode("utf-8")
    return dumps_bytes(data)


def to_jsonable(data: Any) -> Any:
    """Compatibility no-op: return data unchanged."""
    return data
