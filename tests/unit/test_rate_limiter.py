"""Unit tests for rate limiter."""
from __future__ import annotations

import time
import pytest
from core.rate_limiter import TokenBucket, RateLimiter


class TestTokenBucket:
    """Test token bucket rate limiting."""
    
    def test_initial_tokens_at_capacity(self):
        """Test bucket starts at full capacity."""
        bucket = TokenBucket(capacity=10, fill_rate=1.0)
        assert bucket.consume(10) is True
    
    def test_consume_tokens(self):
        """Test token consumption."""
        bucket = TokenBucket(capacity=5, fill_rate=1.0)
        
        assert bucket.consume(3) is True
        assert bucket.consume(2) is True
        assert bucket.consume(1) is False  # Insufficient tokens
    
    def test_tokens_refill_over_time(self):
        """Test tokens refill at specified rate."""
        bucket = TokenBucket(capacity=10, fill_rate=10.0)  # 10 tokens/sec
        
        # Consume all tokens
        bucket.consume(10)
        assert bucket.consume(1) is False
        
        # Wait for refill
        time.sleep(0.2)  # 2 tokens should refill
        assert bucket.consume(2) is True
    
    def test_wait_for_tokens(self):
        """Test waiting for tokens to become available."""
        bucket = TokenBucket(capacity=5, fill_rate=10.0)
        
        # Consume all tokens
        bucket.consume(5)
        
        # Wait for 1 token
        start = time.time()
        result = bucket.wait_for_tokens(1, timeout=1.0)
        duration = time.time() - start
        
        assert result is True
        assert 0.05 < duration < 0.3  # Should wait ~0.1s
    
    def test_wait_timeout(self):
        """Test wait timeout when tokens don't refill in time."""
        bucket = TokenBucket(capacity=5, fill_rate=1.0)  # Slow refill
        
        bucket.consume(5)
        
        result = bucket.wait_for_tokens(10, timeout=0.1)
        assert result is False


class TestRateLimiter:
    """Test rate limiter registry."""
    
    def test_get_creates_limiter(self):
        """Test get() creates new limiter for site."""
        limiter = RateLimiter.get("test_site_1", requests_per_second=5.0)
        assert limiter is not None
    
    def test_get_returns_same_limiter(self):
        """Test get() returns same limiter for same site."""
        limiter1 = RateLimiter.get("test_site_2")
        limiter2 = RateLimiter.get("test_site_2")
        assert limiter1 is limiter2
