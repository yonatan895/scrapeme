"""Type-safe JSON serialization with performance optimization."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from functools import singledispatch
from typing import Any

__all__ = ["to_jsonable"]


@singledispatch
def to_jsonable(obj: Any) -> Any:
    """Recursively convert objects to JSON-serializable primitives."""
    return str(obj)


@to_jsonable.register(type(None))
@to_jsonable.register(bool)
@to_jsonable.register(int)
@to_jsonable.register(float)
@to_jsonable.register(str)
def _jsonable_primitive(obj: None | bool | int | float | str) -> None | bool | int | float | str:
    """Handle primitive types."""
    return obj


@to_jsonable.register(dict)
def _jsonable_dict(obj: dict[Any, Any]) -> dict[str, Any]:
    """Handle dict recursively."""
    return {str(k): to_jsonable(v) for k, v in obj.items()}


@to_jsonable.register(list)
def _jsonable_list(obj: list[Any]) -> list[Any]:
    """Handle list recursively."""
    return [to_jsonable(x) for x in obj]


@to_jsonable.register(tuple)
def _jsonable_tuple(obj: tuple[Any, ...]) -> list[Any]:
    """Handle tuple as list."""
    return [to_jsonable(x) for x in obj]


@to_jsonable.register(set)
def _jsonable_set(obj: set[Any]) -> list[Any]:
    """Handle set as list."""
    return [to_jsonable(x) for x in obj]


_original_to_jsonable = to_jsonable.dispatch(object)


@to_jsonable.register(object)
def _jsonable_object(obj: object) -> Any:
    """Handle objects, checking for dataclasses first."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return to_jsonable(asdict(obj))
    return _original_to_jsonable(obj)
