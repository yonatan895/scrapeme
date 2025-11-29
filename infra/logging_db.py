"""Postgres logging handler."""

from __future__ import annotations

import logging

from infra.db import save_log


class PostgresHandler(logging.Handler):
    """Logging handler that writes to Postgres."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record."""
        try:
            save_log(record)
        except Exception:
            self.handleError(record)
