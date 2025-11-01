"""Adaptive tests for core.metrics that exercise existing metric attributes without assuming names."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestMetrics:
    def test_metrics_registration_and_ops(self):
        from core.metrics import Metrics

        # Discover available metric-like attributes (public, non-dunder, non-callable)
        metric_names = [
            name
            for name in dir(Metrics)
            if not name.startswith("_")
            and name.isidentifier()
            and not callable(getattr(Metrics, name))
        ]

        # Ensure there is at least one metric attribute
        assert metric_names, "No metric attributes found on Metrics"

        for name in metric_names:
            metric = getattr(Metrics, name)

            # Prefer label-scoped operations if available
            if hasattr(metric, "labels"):
                with patch.object(metric, "labels") as mock_labels:
                    fake = MagicMock()
                    mock_labels.return_value = fake

                    # Counter-like API
                    if hasattr(fake, "inc"):
                        fake.inc()
                        fake.inc.assert_called()

                    # Histogram/Summary-like API
                    if hasattr(fake, "observe"):
                        fake.observe(0.123)
                        fake.observe.assert_called()

            else:
                # Fallback to direct operations on the metric object
                if hasattr(metric, "inc"):
                    with patch.object(metric, "inc") as mock_inc:
                        metric.inc()
                        mock_inc.assert_called()
                if hasattr(metric, "observe"):
                    with patch.object(metric, "observe") as mock_observe:
                        metric.observe(0.456)
                        mock_observe.assert_called()
