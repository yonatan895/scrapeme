"""Configuration loading with enhanced validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from config.models import (
    FieldConfig,
    FrameSpec,
    LoginConfig,
    SiteConfig,
    StepBlock,
)
from config.validators import validate_url, validate_xpath
from core.exceptions import ConfigError

__all__ = ["load_sites"]


def _parse_field(data: dict[str, Any]) -> FieldConfig:
    """Parse and validate field configuration."""
    try:
        name = data["name"]
        xpath = data["xpath"]

        if not validate_xpath(xpath):
            raise ConfigError(f"Invalid XPath in field '{name}': {xpath}")

        return FieldConfig(
            name=name,
            xpath=xpath,
            attribute=data.get("attribute"),
        )
    except (KeyError, TypeError) as e:
        raise ConfigError(f"Invalid field configuration: {data}") from e


def _parse_frame(data: dict[str, Any]) -> FrameSpec:
    """Parse and validate frame specification."""
    try:
        spec = FrameSpec(
            xpath=data.get("xpath"),
            css=data.get("css"),
            index=data.get("index"),
            name=data.get("name"),
        )
        return spec
    except ValueError as e:
        raise ConfigError(f"Invalid frame specification: {data}") from e


def _parse_step(data: dict[str, Any]) -> StepBlock:
    """Parse and validate step block."""
    try:
        name = data["name"]

        if goto_url := data.get("goto_url"):
            if not validate_url(goto_url) and not goto_url.startswith("/"):
                raise ConfigError(f"Invalid goto_url in step '{name}': {goto_url}")

        for xpath_field in ["click_xpath", "wait_xpath"]:
            if xpath := data.get(xpath_field):
                if not validate_xpath(xpath):
                    raise ConfigError(f"Invalid {xpath_field} in step '{name}': {xpath}")

        return StepBlock(
            name=name,
            goto_url=goto_url,
            click_xpath=data.get("click_xpath"),
            wait_xpath=data.get("wait_xpath"),
            wait_url_contains=data.get("wait_url_contains"),
            execute_js=data.get("execute_js"),
            fields=tuple(_parse_field(f) for f in data.get("fields", [])),
            frames=tuple(_parse_frame(f) for f in data.get("frames", [])),
            frame_exit=data.get("frame_exit", "default"),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise ConfigError(f"Invalid step: {data.get('name', '<unnamed>')}") from e


def _parse_site(data: dict[str, Any]) -> SiteConfig:
    """Parse and validate site configuration."""
    try:
        name = data["name"]
        base_url = data.get("base_url", "")

        if base_url and not validate_url(base_url):
            raise ConfigError(f"Invalid base_url for site '{name}': {base_url}")

        login = None
        if login_data := data.get("login"):
            if not validate_url(login_data["url"]):
                raise ConfigError(f"Invalid login URL for site '{name}'")
            login = LoginConfig(**login_data)

        return SiteConfig(
            name=name,
            base_url=base_url,
            login=login,
            steps=tuple(_parse_step(s) for s in data.get("steps", [])),
            wait_timeout_sec=int(data.get("wait_timeout_sec", 20)),
            page_load_timeout_sec=int(data.get("page_load_timeout_sec", 30)),
            artifact_dir=data.get("artifact_dir", "artifacts"),
            capture_enabled=data.get("capture_enabled", True),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise ConfigError(f"Invalid site: {data.get('name', '<unnamed>')}") from e


def load_sites(path: Path) -> tuple[SiteConfig, ...]:
    """Load and validate site configurations from YAML."""
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except Exception as e:
        raise ConfigError(f"Failed to load config from {path}") from e

    if not isinstance(data, dict) or "sites" not in data:
        raise ConfigError("Config must have 'sites' key")

    if not isinstance(data["sites"], list):
        raise ConfigError("'sites' must be a list")

    sites = tuple(_parse_site(s) for s in data["sites"])

    names = [s.name for s in sites]
    if len(names) != len(set(names)):
        duplicates = {n for n in names if names.count(n) > 1}
        raise ConfigError(f"Duplicate site names: {duplicates}")

    return sites
