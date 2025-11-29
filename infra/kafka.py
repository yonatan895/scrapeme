"""Kafka producer wrapper."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from kafka import KafkaProducer
from kafka.errors import KafkaError

__all__ = ["get_producer", "send_result", "close_producer"]

_producer: KafkaProducer | None = None
_logger = logging.getLogger("infra.kafka")


def get_producer() -> KafkaProducer | None:
    """Get or create global Kafka producer."""
    global _producer

    if _producer is not None:
        return _producer

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if not bootstrap_servers:
        return None

    try:
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            # Reasonable defaults for reliability vs latency
            acks="all",
            retries=3,
        )
        return _producer
    except Exception as e:
        _logger.error(f"Failed to create Kafka producer: {e}")
        return None


def send_result(site_name: str, data: dict[str, Any]) -> None:
    """Send scrape result to Kafka."""
    producer = get_producer()
    if not producer:
        return

    try:
        # Use a standard topic for all scraped data, partitioned by site name
        topic = os.getenv("KAFKA_TOPIC", "scraped_data")

        future = producer.send(
            topic,
            key=site_name,
            value=data,
        )
        # We don't wait for the future here to avoid blocking the scraping loop too much,
        # but we could add a callback for logging errors.

        def on_error(e: Exception) -> None:
            _logger.error(f"Failed to send to Kafka: {e}")

        future.add_errback(on_error)

    except Exception as e:
        _logger.error(f"Failed to send result to Kafka: {e}")


def close_producer() -> None:
    """Flush and close the Kafka producer."""
    global _producer
    if _producer:
        try:
            _logger.info("Flushing Kafka producer...")
            _producer.flush()
            _producer.close()
            _logger.info("Kafka producer closed")
        except Exception as e:
            _logger.error(f"Error closing Kafka producer: {e}")
        finally:
            _producer = None
