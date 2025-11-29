# Running

Run using compose:

```bash
make compose-up
```

## CLI Reference

The `runner.py` script supports the following arguments:

### Required
- `--config PATH`: Path to the `sites.yaml` configuration file.

### Browser Options
- `--browser {chrome,firefox}`: Browser to use (default: `chrome`).
- `--headless`: Run browser in headless mode (no UI).
- `--incognito`: Use incognito/private browsing mode.
- `--download-dir PATH`: Directory for browser downloads.
- `--remote-url URL`: URL for remote WebDriver (e.g., Selenium Grid).
- `--chromedriver-path PATH`: Specific path to chromedriver executable.
- `--enable-pooling`: Enable WebDriver pooling to reuse sessions between sites (improves performance).

### Execution Control
- `--max-workers INT`: Maximum number of concurrent worker threads (default: 4).
- `--daemon`: Run in daemon mode with health checks (useful for Kubernetes).

### Artifacts & Output
- `--out PATH`: Path for the output file (default: `results.json`).
- `--artifact-dir PATH`: Directory for failure artifacts like screenshots and HTML (default: `artifacts`).
- `--no-artifacts`: Disable artifact generation completely.
- `--jsonl`: Stream output as JSON Lines (one JSON object per line) instead of a single JSON array.
- `--pretty`: Pretty-print the JSON output (slower, but human-readable).

### Observability
- `--metrics-port INT`: Port to expose Prometheus metrics (default: 9090).
- `--log-file PATH`: Path to write logs to a file.
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: `INFO`).
- `--json-logs`: Format logs as JSON for structured logging.

## Outputs

- `results.json` (default): A JSON array containing results for all sites.
- `artifacts/`: Directory containing screenshots and HTML snapshots for failed steps (if enabled).

Example of `results.json`:
```json
[
  {
    "site": "example",
    "data": {
      "title": "Example Domain"
    }
  },
  {
    "site": "failing_site",
    "error": {
      "type": "TimeoutError",
      "message": "Timed out waiting for element",
      "context": {
        "step": "login",
        "xpath": "//input[@id='user']"
      }
    }
  }
]
```
