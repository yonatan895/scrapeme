import time

import pytest


class DummyElement:
    pass


class DummyDriver:
    def __init__(self):
        self._appears_at = None
        self.current_url = "http://example/"

    def mark_visible_at(self, ts):
        self._appears_at = ts

    def is_visible(self):
        return time.time() >= (self._appears_at or 0)

    # Minimal API used by Selenium expected_conditions
    def find_element(self, by=None, value=None):
        return DummyElement()


@pytest.mark.unit
def test_waiter_timeout_behavior():
    from core.waits import Waiter

    driver = DummyDriver()

    # Use a >=1s timeout to satisfy Waiter validation and reduce flakiness
    waiter = Waiter(driver, timeout_sec=1)

    t0 = time.time()
    with pytest.raises(Exception):  # core.exceptions.TimeoutError via url_contains
        waiter.url_contains("never-present-substring")
    assert time.time() - t0 >= 1.0


@pytest.mark.unit
def test_waiter_success(monkeypatch):
    from core.waits import Waiter
    import selenium.webdriver.support.ui as ui

    class FakeWait:
        def __init__(self, driver, timeout):
            pass

        def until(self, condition):
            # Immediately return a sentinel element to simulate success
            class E:
                ...

            return E()

    # Short-circuit WebDriverWait used inside Waiter.visible(...)
    monkeypatch.setattr(ui, "WebDriverWait", FakeWait)

    driver = DummyDriver()
    waiter = Waiter(driver, timeout_sec=1)
    el = waiter.visible(("css selector", "#el"))
    assert el is not None
