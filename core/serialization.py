"""Type-safe JSON serialization with performance optimization."""
from __future__ import annotations

from dataclasses import is_dataclass, asdict
from functools import singledispatch
from typing import Any

__all__ = ["to_jsonable"]


@singledispatch
def to_jsonable(obj: Any) -> Any:
    """Recursively convert objects to JSON-serializable primitives.
    
    Uses singledispatch for O(1) type lookup instead of isinstance chains.
    """
    # Fallback for unknown types
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
def _jsonable_dict(obj: dict) -> dict:
    """Handle dict recursively."""
    return {str(k): to_jsonable(v) for k, v in obj.items()}


@to_jsonable.register(list)
def _jsonable_list(obj: list) -> list:
    """Handle list recursively."""
    return [to_jsonable(x) for x in obj]


@to_jsonable.register(tuple)
def _jsonable_tuple(obj: tuple) -> list:
    """Handle tuple as list."""
    return [to_jsonable(x) for x in obj]


@to_jsonable.register(set)
def _jsonable_set(obj: set) -> list:
    """Handle set as list."""
    return [to_jsonable(x) for x in obj]


# Dataclass handling via custom check
def _is_dataclass_instance(obj: Any) -> bool:
    """Check if object is a dataclass instance."""
    return is_dataclass(obj) and not isinstance(obj, type)


# Override for dataclasses
_original_to_jsonable = to_jsonable.dispatch(object)

@to_jsonable.register(object)
def _jsonable_object(obj: object) -> Any:
    """Handle objects, checking for dataclasses first."""
    if _is_dataclass_instance(obj):
        return to_jsonable(asdict(obj))  # type: ignore
    return _original_to_jsonable(obj)
