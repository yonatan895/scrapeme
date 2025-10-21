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


def setup_signal_handlers():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)


def _handle_signal(signum, frame):
    print(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()
