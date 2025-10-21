"""Chaos engineering tests for network failures."""
from __future__ import annotations

import pytest
import random
from unittest.mock import Mock, patch

from selenium.common.exceptions import WebDriverException

from core.scraper import SiteScraper
from core.circuit_breaker import CircuitBreakerRegistry, CircuitState


@pytest.mark.chaos
class TestNetworkChaos:
    """Chaos tests for network-related failures."""
    
    def test_circuit_breaker_opens_on_repeated_failures(
        self,
        mock_waiter,
        mock_logger,
        sample_site_config,
        tmp_path,
    ):
        """Circuit breaker should open after failure threshold."""
        scraper = SiteScraper(sample_site_config, mock_waiter, mock_logger, artifact_dir=tmp_path)
        
        # Simulate failures
        mock_waiter.driver.get.side_effect = WebDriverException("Network error")
        
        circuit_breaker = CircuitBreakerRegistry.get(sample_site_config.name)
        
        # Execute until circuit opens
        for i in range(10):
            try:
                scraper.run()
            except Exception:
                circuit_breaker.record_failure()
            
            if i >= 5:  # Default failure threshold
                assert circuit_breaker.state == CircuitState.OPEN
                break
    
    def test_intermittent_network_failures_with_retry(
        self,
        mock_waiter,
        mock_logger,
        sample_site_config,
        tmp_path,
    ):
        """Retries should handle intermittent failures."""
        scraper = SiteScraper(sample_site_config, mock_waiter, mock_logger, artifact_dir=tmp_path)
        
        # 50% failure rate
        call_count = 0
        def flaky_get(url):
            nonlocal call_count
            call_count += 1
            if random.random() < 0.5:
                raise WebDriverException("Intermittent failure")
        
        mock_waiter.driver.get.side_effect = flaky_get
        mock_element = Mock()
        mock_element.text = "data"
        mock_waiter.visible.return_value = mock_element
        
        # Should eventually succeed due to retries
        max_attempts = 20
        for _ in range(max_attempts):
            try:
                results = scraper.run()
                assert results is not None
                break
            except WebDriverException:
                continue
        else:
            pytest.fail("Failed after max retry attempts")
    
    def test_timeout_during_page_load(
        self,
        mock_waiter,
        mock_logger,
        sample_site_config,
        tmp_path,
    ):
        """Timeouts should be handled gracefully."""
        from selenium.common.exceptions import TimeoutException
        
        scraper = SiteScraper(sample_site_config, mock_waiter, mock_logger, artifact_dir=tmp_path)
        
        # Simulate page load timeout
        mock_waiter.driver.get.side_effect = TimeoutException("Page load timeout")
        
        with pytest.raises(Exception):
            scraper.run()
        
        # Verify artifacts captured
        artifacts = list(tmp_path.glob("**/*.png"))
        assert len(artifacts) > 0, "Should capture screenshot on timeout"
