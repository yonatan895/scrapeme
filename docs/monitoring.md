# Monitoring the Application

This guide explains how to monitor the `scrapeme` application using Prometheus and Grafana.

## Prometheus

The application exposes a `/metrics` endpoint with Prometheus metrics. The `monitoring/prometheus.yaml` file provides a sample configuration for scraping these metrics.

### Metrics

The following metrics are available:

*   `selenium_scrapes_total`: Total number of scrape attempts.
*   `selenium_scrape_duration_seconds`: Time spent scraping a site.
*   `selenium_steps_executed_total`: Total steps executed.
*   `selenium_step_duration_seconds`: Time spent on a step.
*   `selenium_fields_extracted_total`: Total fields extracted.
*   `selenium_retries_total`: Total retry attempts.
*   `selenium_circuit_breaker_state_changes_total`: Circuit breaker state transitions.
*   `selenium_active_sessions`: Current active WebDriver sessions.
*   `selenium_page_load_duration_seconds`: Page load times.

## Grafana

The `monitoring/grafana/dashboards/selenium-automation.json` file contains a pre-built Grafana dashboard for visualizing the application's metrics.

### 1. Import the Dashboard

To use the dashboard, import it into your Grafana instance.

### 2. Panels

The dashboard includes panels for:

*   Scrape success rate
*   Scrape duration
*   Step duration
*   Active sessions
*   Retry rate
*   Circuit breaker status

## Logging

The application generates structured JSON logs, which can be collected and analyzed by a log management system like Elasticsearch, Loki, or Splunk.

### Log Fields

Each log entry includes the following fields:

*   `timestamp`: The time of the event.
*   `level`: The log level (e.g., `info`, `warning`, `error`).
*   `logger`: The name of the logger.
*   `event`: The log message.
*   `site`: The name of the site being scraped.
*   `step`: The name of the step being executed.
