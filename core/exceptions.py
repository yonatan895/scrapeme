"""Exception hierarchy with structured context and artifact support."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "AutomationError",
    "ConfigError",
    "LoginError",
    "NavigationError",
    "FrameError",
    "ExtractionError",
    "TimeoutError",
    "ElementNotFoundError",
    "ErrorContext",
]


@dataclass(slots=True, frozen=True, kw_only=True)
class ErrorContext:
    """Rich, structured error context for debugging.

    All fields optional; populate only relevant context.
    """

    site_name: str | None = None
    step_name: str | None = None
    field_name: str | None = None
    frame_spec: str | None = None
    url: str | None = None
    xpath: str | None = None
    screenshot: Path | None = None
    html: Path | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class AutomationError(Exception):
    """Base exception with optional structured context."""

    def __init__(
        self,
        message: str,
        *,
        context: ErrorContext | None = None,
    ) -> None:
        super().__init__(message)
        self.context = context or ErrorContext()


class ConfigError(AutomationError):
    """Configuration validation or loading error."""


class LoginError(AutomationError):
    """Authentication or login flow failure."""


class NavigationError(AutomationError):
    """URL navigation or page load failure."""


class FrameError(NavigationError):
    """Frame/iframe switching failure."""


class ExtractionError(AutomationError):
    """Data extraction or field retrieval failure."""


class TimeoutError(AutomationError):
    """Explicit wait timeout (distinct from builtin TimeoutError)."""

    def __init__(
        self,
        message: str,
        *,
        context: ErrorContext | None = None,
        timeout_sec: int | None = None,
    ) -> None:
        super().__init__(message, context=context)
        self.timeout_sec = timeout_sec


class ElementNotFoundError(AutomationError):
    """Element not found after waits and retries."""

    def __init__(
        self,
        message: str,
        *,
        context: ErrorContext | None = None,
        locator: str | None = None,
    ) -> None:
        super().__init__(message, context=context)
        self.locator = locator
