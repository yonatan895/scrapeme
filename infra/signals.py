import signal
import threading

shutdown_event = threading.Event()


def setup_signal_handlers():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)


def _handle_signal(signum, frame):
    print(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()
