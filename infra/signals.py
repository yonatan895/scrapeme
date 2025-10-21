"""Signal handling for graceful shutdown."""

from __future__ import annotations

import signal
import sys
import threading
from types import FrameType
from typing import Callable

__all__ = ["setup_signal_handlers", "shutdown_event", "register_shutdown_handler"]

# Global shutdown event
shutdown_event = threading.Event()

# List of shutdown handlers
_shutdown_handlers: list[Callable[[], None]] = []


def register_shutdown_handler(handler: Callable[[], None]) -> None:
    """Register function to call on shutdown.

    Args:
        handler: Callable that takes no arguments and returns None
    """
    _shutdown_handlers.append(handler)


def _handle_signal(signum: int, frame: FrameType | None) -> None:
    """Handle shutdown signals.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    print(f"\nReceived signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()

    # Call all registered handlers
    for handler in _shutdown_handlers:
        try:
            handler()
        except Exception as e:
            print(f"Shutdown handler failed: {e}", file=sys.stderr)

    sys.exit(0)


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
