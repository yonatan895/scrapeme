"""Custom exception types and error context for scraping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ErrorContext:
    site_name: str | None = None
    step_name: str | None = None
    field_name: str | None = None
    xpath: str | None = None
    url: str | None = None
    frame_spec: str | None = None


class AppTimeoutError(Exception):
    """Application-level timeout distinct from built-in TimeoutError."""

    def __init__(self, message: str, *, timeout_sec: int, context: ErrorContext | None = None):
        super().__init__(message)
        self.timeout_sec = timeout_sec
        self.context = context


class ElementNotFoundError(Exception):
    """Raised when an expected element is not found on the page."""

    def __init__(self, message: str, context: ErrorContext | None = None):
        super().__init__(message)
        self.context = context


class ExtractionError(Exception):
    """Raised when a field extraction fails with contextual data."""

    def __init__(self, message: str, context: ErrorContext | None = None):
        super().__init__(message)
        self.context = context


# Domain-specific higher-level errors referenced across modules
class ConfigError(Exception):
    pass


class FrameError(Exception):
    pass


class LoginError(Exception):
    pass


class AutomationError(Exception):
    pass
