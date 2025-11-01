from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import orjson as _orjson

    def _dumps_bytes(obj: Any, *, pretty: bool = False) -> bytes:
        opt = 0
        if pretty:
            opt |= _orjson.OPT_INDENT_2
        return _orjson.dumps(obj, option=opt)

except Exception:  # pragma: no cover - exercised in fallback test
    import json as _json

    def _dumps_bytes(obj: Any, *, pretty: bool = False) -> bytes:
        return _json.dumps(obj, indent=2 if pretty else None, ensure_ascii=False).encode("utf-8")


_JSON_PRIMITIVES = (str, int, float, bool, type(None))


def to_jsonable(obj: Any) -> Any:
    """Convert objects to JSON-safe structures with minimal work.

    - Leaves JSON primitives as-is.
    - Converts dict/sequence containers iteratively to avoid recursion overhead.
    - Adapts only non-JSON types (Path → str, datetime → ISO 8601, Enum → value).
    - Memoizes by id() to avoid revisiting shared nodes.
    """
    seen: set[int] = set()

    def _adapt_scalar(x: Any) -> Any:
        if isinstance(x, _JSON_PRIMITIVES):
            return x
        if isinstance(x, Path):
            return str(x)
        if isinstance(x, datetime):
            return x.isoformat()
        if isinstance(x, Enum):
            return x.value
        return str(x)

    if isinstance(obj, _JSON_PRIMITIVES):
        return obj

    if isinstance(obj, Mapping):
        root: Any = {}
    elif isinstance(obj, (list, tuple)):
        root = []
    else:
        return _adapt_scalar(obj)

    work: list[tuple[Any, Any]] = [(obj, root)]
    seen.add(id(obj))

    while work:
        src, tgt = work.pop()
        if isinstance(src, Mapping):
            for k, v in src.items():
                key = k if isinstance(k, str) else str(k)
                if isinstance(v, _JSON_PRIMITIVES):
                    tgt[key] = v
                    continue
                if isinstance(v, Mapping):
                    if id(v) in seen:
                        tgt[key] = None
                        continue
                    seen.add(id(v))
                    new_dict: dict[str, Any] = {}
                    tgt[key] = new_dict
                    work.append((v, new_dict))
                elif isinstance(v, (list, tuple)):
                    if id(v) in seen:
                        tgt[key] = None
                        continue
                    seen.add(id(v))
                    new_list: list[Any] = []
                    tgt[key] = new_list
                    work.append((v, new_list))
                else:
                    tgt[key] = _adapt_scalar(v)
        else:  # list/tuple
            for v in src:
                if isinstance(v, _JSON_PRIMITIVES):
                    tgt.append(v)
                    continue
                if isinstance(v, Mapping):
                    if id(v) in seen:
                        tgt.append(None)
                        continue
                    seen.add(id(v))
                    new_dict = {}
                    tgt.append(new_dict)
                    work.append((v, new_dict))
                elif isinstance(v, (list, tuple)):
                    if id(v) in seen:
                        tgt.append(None)
                        continue
                    seen.add(id(v))
                    child_list: list[Any] = []
                    tgt.append(child_list)
                    work.append((v, child_list))
                else:
                    tgt.append(_adapt_scalar(v))

    return root


def dumps(obj: Any, *, pretty: bool = False) -> bytes:
    """Serialize to bytes using orjson if available, else stdlib json.

    The input should already be JSON-safe (use to_jsonable first for non-JSON types).
    """
    return _dumps_bytes(obj, pretty=pretty)
