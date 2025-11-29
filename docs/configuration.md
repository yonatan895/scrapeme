# Configuration (sites.yaml)

Configuration is a YAML document that defines one or more sites to process. The structure is validated against typed models in `config/models.py`.

```yaml
sites:
  - name: example
    base_url: "https://example.com"
    wait_timeout_sec: 20
    page_load_timeout_sec: 30
    capture_enabled: true     # Enable/disable artifact capture for this site
    artifact_dir: "artifacts" # Directory for artifacts (relative to global artifact dir)
    login:                    # Optional; see Login Config below
      url: "https://example.com/login"
      username_xpath: "//input[@name='u']"
      password_xpath: "//input[@name='p']"
      submit_xpath:   "//button[@type='submit']"
      username_env: "EXAMPLE_USER"
      password_env: "EXAMPLE_PASS"
    steps:
      - name: homepage
        goto_url: "https://example.com" # Optional navigation
        wait_xpath: "//h1"              # Wait for element presence
        fields:
          - name: title
            xpath: "//h1"
```

## Site Configuration (`SiteConfig`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | **Required** | Unique identifier for the site. |
| `base_url` | string | **Required** | Base URL, used for metrics and navigation. |
| `login` | LoginConfig | None | Optional login configuration. |
| `steps` | List[StepBlock] | [] | Ordered list of scraping steps. |
| `wait_timeout_sec` | int | 20 | Default timeout for explicit waits (seconds). |
| `page_load_timeout_sec` | int | 30 | Timeout for page loads (seconds). |
| `capture_enabled` | bool | True | Enable screenshot/HTML capture on failure. |
| `artifact_dir` | string | "artifacts" | Subdirectory for site artifacts. |

## Login Configuration (`LoginConfig`)

Credentials are loaded from environment variables specified by `username_env` and `password_env`.

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Login page URL. |
| `username_xpath` | string | XPath for username input. |
| `password_xpath` | string | XPath for password input. |
| `submit_xpath` | string | XPath for submit button. |
| `username_env` | string | Env var name for username. |
| `password_env` | string | Env var name for password. |
| `post_login_wait_xpath` | string | Optional XPath to wait for after login (verifies success). |
| `post_login_url_contains` | string | Optional URL substring to wait for after login. |

## Step Configuration (`StepBlock`)

Steps are executed in order. A step can navigate, interact, wait, and extract data.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique step identifier. |
| `goto_url` | string | Optional URL to navigate to at start of step. |
| `click_xpath` | string | Optional XPath of element to click. |
| `wait_xpath` | string | Optional XPath to wait for visibility. |
| `wait_url_contains` | string | Optional URL substring to wait for. |
| `execute_js` | string | Optional JavaScript code to execute. |
| `fields` | List[FieldConfig] | Data fields to extract. |
| `frames` | List[FrameSpec] | Frames to enter before extraction. |
| `frame_exit` | "default" \| "parent" | How to exit frames ("default" = top level). |

## Field Configuration (`FieldConfig`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique field name. |
| `xpath` | string | XPath selector for the element. |
| `attribute` | string | Optional attribute to extract (e.g., "href", "src"). If omitted, extracts text content. |

## Frame Specification (`FrameSpec`)

Used to switch context into an `<iframe>`. Exactly one selector must be provided.

| Field | Type | Description |
|-------|------|-------------|
| `xpath` | string | XPath selector for the iframe. |
| `css` | string | CSS selector for the iframe. |
| `index` | int | Zero-based index of the frame. |
| `name` | string | Name attribute of the frame. |

### Example with Frames

```yaml
    steps:
      - name: widget_data
        frames:
          - xpath: "//iframe[@id='widget']"
        fields:
          - name: widget_title
            xpath: "//div[@class='title']"
```
