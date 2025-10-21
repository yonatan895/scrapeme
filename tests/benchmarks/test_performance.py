"""Performance benchmarks."""

from __future__ import annotations

import pytest

from config.models import FieldConfig, StepBlock
from core.serialization import to_jsonable
from core.url import normalize_url


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for critical paths."""

    def test_url_normalization_benchmark(self, benchmark):
        """Benchmark URL normalization with caching."""
        url = "https://example.com/path?query=value"
        result = benchmark(normalize_url, url)
        assert result == url

    def test_serialization_benchmark(self, benchmark):
        """Benchmark JSON serialization."""
        data = {
            "site": "test",
            "steps": [{"name": f"step_{i}", "data": {"field": f"value_{i}"}} for i in range(100)],
        }
        result = benchmark(to_jsonable, data)
        assert len(result["steps"]) == 100

    def test_field_config_creation_benchmark(self, benchmark):
        """Benchmark field config creation."""
        result = benchmark(
            FieldConfig,
            name="test_field",
            xpath="//div[@class='test']",
        )
        assert result.name == "test_field"

    def test_step_block_creation_benchmark(self, benchmark):
        """Benchmark step block creation with multiple fields."""
        fields = tuple(FieldConfig(name=f"field_{i}", xpath=f"//div[@id='{i}']") for i in range(10))

        result = benchmark(
            StepBlock,
            name="test_step",
            fields=fields,
        )
        assert len(result.fields) == 10
