"""Secrets management utilities and provider protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SecretProvider(Protocol):
    def get(self, name: str) -> str | None:  # noqa: D401
        """Return secret by name if available."""
        ...


@dataclass(slots=True)
class EnvSecrets:
    """Access secrets from environment or external stores."""

    def get(self, name: str) -> str | None:  # noqa: D401
        """Return secret by name if available."""
        import os

        return os.getenv(name)

    def from_vault(self, *, vault_addr: str | None = None, vault_token: str | None = None) -> "EnvSecrets":
        """Initialize retrieval from Vault (placeholder)."""
        _ = (vault_addr, vault_token)
        return self
