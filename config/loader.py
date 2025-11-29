"""Configuration loading with enhanced validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from config.models import SiteConfig
from core.exceptions import ConfigError

__all__ = ["load_sites"]


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

    sites: list[SiteConfig] = []
    for site_data in data["sites"]:
        try:
            site = SiteConfig(**site_data)
            sites.append(site)
        except ValidationError as e:
            site_name = site_data.get("name", "<unnamed>")
            # Simplify error message or pass structured error?
            # For now, providing a clean error message
            error_msgs = []
            for error in e.errors():
                loc = " -> ".join(str(l) for l in error["loc"])
                msg = error["msg"]
                error_msgs.append(f"{loc}: {msg}")

            raise ConfigError(f"Invalid site configuration for '{site_name}': " + "; ".join(error_msgs)) from e
        except Exception as e:
            site_name = site_data.get("name", "<unnamed>")
            raise ConfigError(f"Invalid site: {site_name}") from e

    names = [s.name for s in sites]
    if len(names) != len(set(names)):
        duplicates = {n for n in names if names.count(n) > 1}
        raise ConfigError(f"Duplicate site names: {duplicates}")

    return tuple(sites)
