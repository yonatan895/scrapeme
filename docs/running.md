# Running & CLI

The entry point is runner.py with an ergonomic CLI.

```bash
python runner.py --config config/sites.yaml \
  --browser chrome --headless \
  --out results.json --json-logs \
  --max-workers 4 --enable-pooling
```

Important flags:
- --config PATH            — required sites.yaml
- --browser chrome|firefox — default chrome
- --headless               — run without UI
- --incognito              — private sessions
- --download-dir PATH      — browser downloads
- --artifact-dir PATH      — artifacts (screens, HTML)
- --no-artifacts           — disable artifacts
- --jsonl                  — stream one JSON per line
- --pretty                 — pretty output (slower)
- --metrics-port 9090      — Prometheus metrics

Outputs:
- results.json (default) or JSONL stream
- artifacts/ (screenshots, HTML) when enabled
