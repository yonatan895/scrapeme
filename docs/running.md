# Running 
Run using compose:

```bash
make compose-up
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
