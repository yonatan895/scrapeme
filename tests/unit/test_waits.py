import time

import pytest


class DummyDriver:
    def __init__(self):
        self._appears_at = None

    def mark_visible_at(self, ts):
        self._appears_at = ts

    def is_visible(self):
        # simplistic probe used by the waiter stub
        return time.time() >= (self._appears_at or 0)


@pytest.mark.unit
def test_waiter_timeout_behavior(monkeypatch):
    from core.waits import Waiter

    driver = DummyDriver()

    # monkeypatch a probe function used by Waiter.wait_for(lambda)
    def probe():
        return driver.is_visible()

    waiter = Waiter(driver, timeout_sec=0.2)
    t0 = time.time()
    with pytest.raises(TimeoutError):
        waiter.wait_for(probe)
    assert time.time() - t0 >= 0.2


@pytest.mark.unit
def test_waiter_success(monkeypatch):
    from core.waits import Waiter

    driver = DummyDriver()

    def probe():
        return driver.is_visible()

    waiter = Waiter(driver, timeout_sec=1.0)

    # Make element appear shortly
    driver.mark_visible_at(time.time() + 0.1)
    waiter.wait_for(probe)  # should not raise
