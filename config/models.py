"""Typed configuration models with strict immutability and validation."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from config.validators import validate_url, validate_xpath

__all__ = [
    "Browser",
    "FieldConfig",
    "LoginConfig",
    "FrameSpec",
    "StepBlock",
    "SiteConfig",
]


class Browser(StrEnum):
    """Supported browser types."""

    CHROME = "chrome"
    FIREFOX = "firefox"


class FieldConfig(BaseModel):
    """Single field extraction specification.

    Attributes:
        name: Unique identifier for this field within its step
        xpath: XPath selector for the element
        attribute: Optional attribute name; None uses element.text
    """

    name: str = Field(min_length=1)
    xpath: str = Field(min_length=1)
    attribute: str | None = None

    @field_validator("xpath")
    @classmethod
    def validate_xpath_field(cls, v: str) -> str:
        """Validate XPath syntax."""
        if not validate_xpath(v):
            raise ValueError(f"Invalid XPath: {v}")
        return v

    model_config = {"frozen": True, "extra": "forbid"}


class LoginConfig(BaseModel):
    """Authentication flow specification.

    Attributes:
        url: Login page URL
        username_xpath: XPath for username input field
        password_xpath: XPath for password input field
        submit_xpath: XPath for submit button
        username_env: Environment variable name for username
        password_env: Environment variable name for password
        post_login_wait_xpath: Optional XPath to wait for after login
        post_login_url_contains: Optional URL substring to verify after login
    """

    url: str
    username_xpath: str
    password_xpath: str
    submit_xpath: str
    username_env: str = Field(min_length=1)
    password_env: str = Field(min_length=1)
    post_login_wait_xpath: str | None = None
    post_login_url_contains: str | None = None

    @field_validator("url")
    @classmethod
    def validate_login_url(cls, v: str) -> str:
        """Validate login URL."""
        if not validate_url(v):
            raise ValueError(f"Invalid URL: {v}")
        return v

    model_config = {"frozen": True, "extra": "forbid"}


class FrameSpec(BaseModel):
    """Frame/iframe selection specification.

    Exactly one selector must be non-None.
    """

    xpath: str | None = None
    css: str | None = None
    index: int | None = Field(None, ge=0)
    name: str | None = None

    @model_validator(mode="after")
    def validate_selectors(self) -> FrameSpec:
        """Validate exactly one selector is provided."""
        selectors = (self.xpath, self.css, self.index, self.name)
        provided_count = sum(s is not None for s in selectors)

        if provided_count == 0:
            raise ValueError("FrameSpec requires at least one selector: xpath, css, index, or name")
        if provided_count > 1:
            raise ValueError("FrameSpec requires exactly one selector, got multiple")
        return self

    model_config = {"frozen": True, "extra": "forbid"}


class StepBlock(BaseModel):
    """Navigation and extraction step."""

    name: str = Field(min_length=1)
    goto_url: str | None = None
    click_xpath: str | None = None
    wait_xpath: str | None = None
    wait_url_contains: str | None = None
    execute_js: str | None = None
    fields: tuple[FieldConfig, ...] = Field(default_factory=tuple)
    frames: tuple[FrameSpec, ...] = Field(default_factory=tuple)
    frame_exit: Literal["default", "parent"] = "default"

    @field_validator("goto_url")
    @classmethod
    def validate_goto_url(cls, v: str | None) -> str | None:
        """Validate goto_url."""
        if v and not validate_url(v) and not v.startswith("/"):
            raise ValueError(f"Invalid goto_url: {v}")
        return v

    @field_validator("click_xpath", "wait_xpath")
    @classmethod
    def validate_step_xpaths(cls, v: str | None) -> str | None:
        """Validate step XPaths."""
        if v and not validate_xpath(v):
            raise ValueError(f"Invalid XPath: {v}")
        return v

    @field_validator("fields")
    @classmethod
    def validate_unique_fields(cls, v: tuple[FieldConfig, ...]) -> tuple[FieldConfig, ...]:
        """Validate unique field names within step."""
        field_names = [f.name for f in v]
        if len(field_names) != len(set(field_names)):
            duplicates = {n for n in field_names if field_names.count(n) > 1}
            raise ValueError(f"Duplicate field names in step: {duplicates}")
        return v

    model_config = {"frozen": True, "extra": "forbid"}


class SiteConfig(BaseModel):
    """Complete site automation specification."""

    name: str = Field(min_length=1)
    base_url: str
    login: LoginConfig | None = None
    steps: tuple[StepBlock, ...] = Field(default_factory=tuple)
    wait_timeout_sec: int = Field(default=20, gt=0)
    page_load_timeout_sec: int = Field(default=30, gt=0)
    artifact_dir: str = "artifacts"
    capture_enabled: bool = True

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL."""
        if not validate_url(v):
            raise ValueError(f"Invalid base_url: {v}")
        return v

    @field_validator("steps")
    @classmethod
    def validate_unique_step_names(cls, v: tuple[StepBlock, ...]) -> tuple[StepBlock, ...]:
        """Validate unique step names within site."""
        step_names = [step.name for step in v]
        if len(step_names) != len(set(step_names)):
            duplicates = {n for n in step_names if step_names.count(n) > 1}
            raise ValueError(f"Duplicate step names in site: {duplicates}")
        return v

    @field_validator("artifact_dir")
    @classmethod
    def validate_artifact_dir(cls, v: str) -> str:
        """Validate artifact_dir is safe."""
        if not v or any(c in v for c in ["/", "\\", "\0"]):
            raise ValueError(f"Invalid artifact_dir: {v}")
        return v

    @property
    def total_fields(self) -> int:
        """Total number of fields across all steps."""
        return sum(len(step.fields) for step in self.steps)

    @property
    def has_login(self) -> bool:
        """Check if site has login configuration."""
        return self.login is not None

    @property
    def has_frames(self) -> bool:
        """Check if any step uses frames."""
        return any(step.frames for step in self.steps)

    model_config = {"frozen": True, "extra": "forbid"}
