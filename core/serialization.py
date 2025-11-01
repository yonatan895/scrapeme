"""Serialization helpers for stable JSON encoding/decoding."""

from __future__ import annotations

from typing import Any

try:
    import orjson as _json
    _HAS_ORJSON = True
except Exception:  # pragma: no cover - fallback path
    import json as _json  # type: ignore[no-redef]
    _HAS_ORJSON = False


def dumps(data: Any) -> bytes | str:
    """Serialize data to JSON.

    Returns bytes when using orjson, str when falling back to stdlib json.
    """
    if _HAS_ORJSON and hasattr(_json, "dumps"):
        # Use default options if OPT_INDENT_2 not present in orjson build
        opts = getattr(_json, "OPT_INDENT_2", 0)
        return _json.dumps(data, option=opts)  # type: ignore[call-arg]
    # Stdlib json fallback
    return _json.dumps(data).encode("utf-8")


def pretty_dumps(data: Any) -> str:
    """Pretty-print JSON for logs and artifacts."""
    if _HAS_ORJSON:
        return _json.dumps(data, option=getattr(_json, "OPT_INDENT_2", 0)).decode("utf-8")  # type: ignore[call-arg]
    return _json.dumps(data, indent=2)


def loads(data: bytes | str) -> Any:
    """Deserialize data from JSON."""
    if isinstance(data, (bytes, bytearray)):
        try:
            return _json.loads(data)
        except Exception:  # pragma: no cover
            return _json.loads(data.decode("utf-8"))
    return _json.loads(data)
