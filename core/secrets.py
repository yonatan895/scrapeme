"""Secret provider abstraction with multiple backends."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

__all__ = ["SecretProvider", "EnvSecrets", "FileSecrets", "VaultSecrets"]


class SecretProvider(Protocol):
    """Protocol for secret retrieval.

    Implementations must be thread-safe for concurrent site processing.
    """

    def get(self, key: str) -> str | None:
        """Retrieve secret by key.

        Args:
            key: Secret identifier

        Returns:
            Secret value or None if not found
        """
        ...


class EnvSecrets:
    """Environment variable-based secret provider.

    Thread-safe via os.environ access.
    """

    __slots__ = ()

    def get(self, key: str) -> str | None:
        """Retrieve from process environment."""
        return os.getenv(key)


class FileSecrets:
    """File-based secret provider for local development.

    Reads secrets from a directory structure like:
    /secrets/
        USERNAME
        PASSWORD

    Compatible with Kubernetes mounted secrets.
    """

    __slots__ = ("_secrets_dir",)

    def __init__(self, secrets_dir: Path) -> None:
        """Initialize file-based secrets.

        Args:
            secrets_dir: Directory containing secret files
        """
        self._secrets_dir = secrets_dir

    def get(self, key: str) -> str | None:
        """Retrieve from file system."""
        secret_file = self._secrets_dir / key
        if secret_file.exists():
            return secret_file.read_text(encoding="utf-8").strip()
        return None


class VaultSecrets:
    """HashiCorp Vault secret provider (stub for production).

    In production, integrate with hvac library:
    https://github.com/hvac/hvac
    """

    __slots__ = ("_vault_client", "_mount_point", "_secret_path")

    def __init__(
        self,
        vault_addr: str,
        vault_token: str,
        mount_point: str = "secret",
        secret_path: str = "selenium",
    ) -> None:
        """Initialize Vault client.

        Args:
            vault_addr: Vault server address
            vault_token: Authentication token
            mount_point: KV mount point
            secret_path: Path to secrets
        """
        # Stub implementation - integrate hvac in production
        self._vault_client = None  # hvac.Client(url=vault_addr, token=vault_token)
        self._mount_point = mount_point
        self._secret_path = secret_path

    def get(self, key: str) -> str | None:
        """Retrieve from Vault."""
        # Stub - implement with hvac
        # response = self._vault_client.secrets.kv.v2.read_secret_version(
        #     path=f"{self._secret_path}/{key}",
        #     mount_point=self._mount_point,
        # )
        # return response["data"]["data"].get(key)
        raise NotImplementedError("VaultSecrets requires hvac library integration")


class ChainedSecrets:
    """Chain multiple secret providers with fallback.

    Example:
        secrets = ChainedSecrets([
            EnvSecrets(),
            FileSecrets(Path("/run/secrets")),
        ])
    """

    __slots__ = ("_providers",)

    def __init__(self, providers: list[SecretProvider]) -> None:
        """Initialize chained provider.

        Args:
            providers: List of providers to try in order
        """
        self._providers = providers

    def get(self, key: str) -> str | None:
        """Try each provider until secret found."""
        for provider in self._providers:
            if value := provider.get(key):
                return value
        return None
