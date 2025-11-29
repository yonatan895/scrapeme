"""Postgres storage backend with connection pooling."""

from __future__ import annotations

import contextlib
import json
import logging
import os
from typing import Any, Generator

import psycopg2
from psycopg2 import pool
from psycopg2.extras import Json

__all__ = ["init_db", "save_result", "save_log", "close_db"]

_pool: psycopg2.pool.ThreadedConnectionPool | None = None
_logger = logging.getLogger("infra.db")


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool | None:
    """Get or create the connection pool."""
    global _pool
    if _pool is not None:
        return _pool

    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        return None

    try:
        # Min 1, Max 10 connections
        _pool = psycopg2.pool.ThreadedConnectionPool(1, 10, dsn)
        return _pool
    except Exception as e:
        _logger.error(f"Failed to create Postgres connection pool: {e}")
        return None


@contextlib.contextmanager
def get_cursor() -> Generator[Any, None, None]:
    """Context manager to get a cursor from the pool."""
    pool = _get_pool()
    if not pool:
        yield None
        return

    conn = None
    try:
        conn = pool.getconn()
        with conn:
            with conn.cursor() as cur:
                yield cur
    except Exception as e:
        _logger.error(f"Database operation failed: {e}")
        # If the connection is broken, we might want to discard it?
        # But for now, just logging.
        if conn:
            # Maybe rollback if needed, but 'with conn' handles commit/rollback
            pass
        raise
    finally:
        if conn:
            pool.putconn(conn)


def init_db() -> None:
    """Initialize database schema."""
    try:
        with get_cursor() as cur:
            if cur is None:
                _logger.warning("Postgres not configured - skipping DB init")
                return

            # Create results table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scrape_results (
                    id SERIAL PRIMARY KEY,
                    site_name VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    data JSONB NOT NULL
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_results_site ON scrape_results(site_name);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_results_ts ON scrape_results(timestamp);")

            # Create logs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scrape_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    level VARCHAR(50) NOT NULL,
                    logger_name VARCHAR(255),
                    message TEXT,
                    context JSONB
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_ts ON scrape_logs(timestamp);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON scrape_logs(level);")

        _logger.info("Database initialized successfully")
    except Exception:
        _logger.error("Failed to initialize database", exc_info=True)


def save_result(site_name: str, data: dict[str, Any]) -> None:
    """Save scrape result to Postgres."""
    try:
        with get_cursor() as cur:
            if cur is None:
                return

            cur.execute(
                """
                INSERT INTO scrape_results (site_name, data)
                VALUES (%s, %s)
                """,
                (site_name, Json(data))
            )
    except Exception:
        # Error already logged by context manager
        pass


def save_log(record: logging.LogRecord) -> None:
    """Save log record to Postgres."""
    # Avoid infinite recursion if the DB logger logs itself
    if record.name == "infra.db":
        return

    try:
        # Be careful not to block too long in logging
        # Check if pool exists first to avoid overhead
        if _pool is None and not os.getenv("POSTGRES_DSN"):
            return

        with get_cursor() as cur:
            if cur is None:
                return

            context = {
                "file": record.filename,
                "line": record.lineno,
                "func": record.funcName,
            }

            cur.execute(
                """
                INSERT INTO scrape_logs (timestamp, level, logger_name, message, context)
                VALUES (to_timestamp(%s), %s, %s, %s, %s)
                """,
                (
                    record.created,
                    record.levelname,
                    record.name,
                    record.getMessage(),
                    Json(context)
                )
            )
    except Exception:
        # Don't propagate logging errors
        pass


def close_db() -> None:
    """Close the connection pool."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
