"""Typed configuration models with strict immutability and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

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


@dataclass(slots=True, frozen=True, kw_only=True)
class FieldConfig:
    """Single field extraction specification.

    Attributes:
        name: Unique identifier for this field within its step
        xpath: XPath selector for the element
        attribute: Optional attribute name; None uses element.text

    Examples:
        # Extract text content
        FieldConfig(name="title", xpath="//h1[@class='page-title']")

        # Extract attribute
        FieldConfig(name="link", xpath="//a[@id='next']", attribute="href")
    """

    name: str
    xpath: str
    attribute: str | None = None

    def __post_init__(self) -> None:
        """Validate field configuration."""
        if not self.name or not self.name.strip():
            raise ValueError("Field name cannot be empty")
        if not self.xpath or not self.xpath.strip():
            raise ValueError("Field xpath cannot be empty")


@dataclass(slots=True, frozen=True, kw_only=True)
class LoginConfig:
    """Authentication flow specification.

    All XPath selectors must be absolute or well-qualified.
    Credentials are loaded from environment variables at runtime.

    Attributes:
        url: Login page URL
        username_xpath: XPath for username input field
        password_xpath: XPath for password input field
        submit_xpath: XPath for submit button
        username_env: Environment variable name for username
        password_env: Environment variable name for password
        post_login_wait_xpath: Optional XPath to wait for after login
        post_login_url_contains: Optional URL substring to verify after login

    Example:
        LoginConfig(
            url="https://example.com/login",
            username_xpath="//input[@id='username']",
            password_xpath="//input[@id='password']",
            submit_xpath="//button[@type='submit']",
            username_env="EXAMPLE_USER",
            password_env="EXAMPLE_PASS",
            post_login_wait_xpath="//div[@id='dashboard']",
        )
    """

    url: str
    username_xpath: str
    password_xpath: str
    submit_xpath: str
    username_env: str
    password_env: str
    post_login_wait_xpath: str | None = None
    post_login_url_contains: str | None = None

    def __post_init__(self) -> None:
        """Validate login configuration."""
        if not self.url:
            raise ValueError("Login URL cannot be empty")
        if not self.username_env or not self.password_env:
            raise ValueError("Credential environment variables cannot be empty")


@dataclass(slots=True, frozen=True, kw_only=True)
class FrameSpec:
    """Frame/iframe selection specification.

    Exactly one selector must be non-None. Validated at initialization.

    Attributes:
        xpath: XPath selector for frame
        css: CSS selector for frame
        index: Zero-based frame index
        name: Frame name attribute

    Examples:
        # By XPath
        FrameSpec(xpath="//iframe[@id='content']")

        # By CSS
        FrameSpec(css="iframe.main-content")

        # By index (including 0)
        FrameSpec(index=0)

        # By name
        FrameSpec(name="mainFrame")
    """

    xpath: str | None = None
    css: str | None = None
    index: int | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        """Validate exactly one selector is provided."""
        selectors = (self.xpath, self.css, self.index, self.name)
        provided_count = sum(s is not None for s in selectors)

        if provided_count == 0:
            raise ValueError("FrameSpec requires at least one selector: xpath, css, index, or name")
        if provided_count > 1:
            raise ValueError("FrameSpec requires exactly one selector, got multiple")

        # Validate index is non-negative if provided
        if self.index is not None and self.index < 0:
            raise ValueError(f"Frame index must be non-negative, got {self.index}")


@dataclass(slots=True, frozen=True, kw_only=True)
class StepBlock:
    """Navigation and extraction step.

    Execution order:
        1. goto_url (if specified)
        2. Enter frames (if specified)
        3. execute_js (if specified)
        4. click_xpath (if specified)
        5. wait_xpath (if specified)
        6. wait_url_contains (if specified)
        7. Extract all fields
        8. Exit frames

    Attributes:
        name: Unique step identifier within site
        goto_url: Optional URL to navigate to
        click_xpath: Optional element to click
        wait_xpath: Optional element to wait for visibility
        wait_url_contains: Optional URL substring to wait for
        execute_js: Optional JavaScript to execute
        fields: Tuple of fields to extract
        frames: Tuple of frames to enter (outer → inner)
        frame_exit: Exit strategy ("default" returns to main document, "parent" goes up one level)

    Example:
        StepBlock(
            name="product_details",
            goto_url="https://example.com/products/123",
            wait_xpath="//div[@class='product-loaded']",
            fields=(
                FieldConfig(name="title", xpath="//h1[@class='product-title']"),
                FieldConfig(name="price", xpath="//span[@class='price']"),
            ),
        )
    """

    name: str
    goto_url: str | None = None
    click_xpath: str | None = None
    wait_xpath: str | None = None
    wait_url_contains: str | None = None
    execute_js: str | None = None
    fields: tuple[FieldConfig, ...] = ()
    frames: tuple[FrameSpec, ...] = ()
    frame_exit: Literal["default", "parent"] = "default"

    def __post_init__(self) -> None:
        """Validate step configuration."""
        if not self.name or not self.name.strip():
            raise ValueError("Step name cannot be empty")

        # Validate frame_exit
        if self.frame_exit not in ("default", "parent"):
            raise ValueError(f"Invalid frame_exit: {self.frame_exit}")

        # Ensure fields is tuple (defensive)
        if not isinstance(self.fields, tuple):
            object.__setattr__(self, "fields", tuple(self.fields))

        # Ensure frames is tuple (defensive)
        if not isinstance(self.frames, tuple):
            object.__setattr__(self, "frames", tuple(self.frames))

        # Validate unique field names within step
        field_names = [f.name for f in self.fields]
        if len(field_names) != len(set(field_names)):
            duplicates = {n for n in field_names if field_names.count(n) > 1}
            raise ValueError(f"Duplicate field names in step '{self.name}': {duplicates}")


@dataclass(slots=True, frozen=True, kw_only=True)
class SiteConfig:
    """Complete site automation specification.

    Attributes:
        name: Unique site identifier
        base_url: Base URL to navigate to before steps (optional)
        login: Optional login configuration
        steps: Tuple of steps to execute in order
        wait_timeout_sec: Default timeout for explicit waits (seconds)
        page_load_timeout_sec: Timeout for page loads (seconds)
        artifact_dir: Directory name for failure artifacts (relative to base artifact dir)
        capture_enabled: Enable/disable artifact capture for this site

    Example:
        SiteConfig(
            name="example_site",
            base_url="https://example.com",
            login=LoginConfig(...),
            steps=(
                StepBlock(name="homepage", ...),
                StepBlock(name="products", ...),
            ),
            wait_timeout_sec=20,
            page_load_timeout_sec=30,
        )
    """

    name: str
    base_url: str
    login: LoginConfig | None = None
    steps: tuple[StepBlock, ...] = ()
    wait_timeout_sec: int = 20
    page_load_timeout_sec: int = 30
    artifact_dir: str = "artifacts"
    capture_enabled: bool = True

    def __post_init__(self) -> None:
        """Validate site configuration constraints."""
        if not self.name or not self.name.strip():
            raise ValueError("Site name cannot be empty")

        if self.wait_timeout_sec < 1:
            raise ValueError(f"wait_timeout_sec must be positive, got {self.wait_timeout_sec}")

        if self.page_load_timeout_sec < 1:
            raise ValueError(
                f"page_load_timeout_sec must be positive, got {self.page_load_timeout_sec}"
            )

        # Ensure steps is tuple (defensive)
        if not isinstance(self.steps, tuple):
            object.__setattr__(self, "steps", tuple(self.steps))

        # Enforce unique step names within site
        step_names = [step.name for step in self.steps]
        if len(step_names) != len(set(step_names)):
            duplicates = {n for n in step_names if step_names.count(n) > 1}
            raise ValueError(f"Duplicate step names in site '{self.name}': {duplicates}")

        # Validate artifact_dir is safe for filesystem
        if not self.artifact_dir or any(c in self.artifact_dir for c in ["/", "\\", "\0"]):
            raise ValueError(f"Invalid artifact_dir: {self.artifact_dir}")

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
