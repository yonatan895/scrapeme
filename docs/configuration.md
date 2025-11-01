# Configuration (sites.yaml)

Configuration is a YAML document that defines one or more sites to process.

```yaml
sites:
  - name: example
    base_url: "https://example.com"
    wait_timeout_sec: 20
    page_load_timeout_sec: 30
    login:            # optional; see core/auth
      username_xpath: "//input[@name='u']"
      password_xpath: "//input[@name='p']"
      submit_xpath:   "//button[@type='submit']"
    steps:
      - name: homepage
        goto_url: "https://example.com"
        wait_xpath: "//h1"
        fields:
          - name: title
            xpath: "//h1"
```

Key fields:
- name — unique site id
- base_url — used by metrics and navigation helpers
- wait_timeout_sec / page_load_timeout_sec — Selenium timeouts
- login — declarative login flow (optional)
- steps — ordered actions and selectors (handled by core/scraper)

Validation occurs at load time via config/models.py. Keep selectors stable and prefer resilient XPaths.
