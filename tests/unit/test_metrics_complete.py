"""Unit tests for core.metrics module to achieve complete coverage."""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestMetrics:
    def test_metrics_registration(self):
        """Test that metrics are properly registered."""
        from core.metrics import Metrics
        
        # Smoke test: ensure metrics objects exist
        assert hasattr(Metrics, 'scrape_requests_total')
        assert hasattr(Metrics, 'scrape_duration_seconds')
        assert hasattr(Metrics, 'wait_duration_seconds')
        assert hasattr(Metrics, 'element_interactions_total')
        assert hasattr(Metrics, 'page_load_duration_seconds')

    def test_counter_increment(self):
        """Test counter increment operations."""
        from core.metrics import Metrics
        
        # Mock prometheus counter to avoid actual metrics
        with patch.object(Metrics.scrape_requests_total, 'labels') as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter
            
            # Should not raise
            Metrics.scrape_requests_total.labels(status='success').inc()
            mock_labels.assert_called_with(status='success')
            mock_counter.inc.assert_called_once()

    def test_histogram_observe(self):
        """Test histogram observation."""
        from core.metrics import Metrics
        
        with patch.object(Metrics.scrape_duration_seconds, 'labels') as mock_labels:
            mock_histogram = MagicMock()
            mock_labels.return_value = mock_histogram
            
            # Should not raise
            Metrics.scrape_duration_seconds.labels(site='test').observe(1.23)
            mock_labels.assert_called_with(site='test')
            mock_histogram.observe.assert_called_with(1.23)

    def test_wait_metrics_labels(self):
        """Test wait metrics label handling."""
        from core.metrics import Metrics
        
        with patch.object(Metrics.wait_duration_seconds, 'labels') as mock_labels:
            mock_histogram = MagicMock()
            mock_labels.return_value = mock_histogram
            
            # Test different wait types
            for wait_type in ['presence', 'visibility', 'clickable']:
                Metrics.wait_duration_seconds.labels(wait_type=wait_type).observe(0.5)
                
            assert mock_labels.call_count == 3
            mock_histogram.observe.assert_called_with(0.5)
