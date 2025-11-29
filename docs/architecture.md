# Architecture Overview

## High Level Flow

1.  **Entry Point (`runner.py`)**:
    -   Parses CLI arguments.
    -   Loads and validates configuration (`config/loader`).
    -   Starts the Health Server (`infra/server`).
    -   Initializes the `ThreadPoolExecutor`.

2.  **Execution (`process_site`)**:
    -   Checks **Circuit Breaker** status for the site.
    -   Instantiates `BrowserManager` to obtain a WebDriver.
    -   Performs **Authentication** (if configured) via `core/auth`.
    -   Executes scraping steps via `core/scraper`.
    -   Records metrics (success/failure, duration).

3.  **Core Components**:
    -   **Scraping**: `core/scraper.SiteScraper` manages the flow of steps, frame switching, and data extraction.
    -   **Waiting**: `core/waits.Waiter` handles smart explicit waits for elements and states.
    -   **Artifacts**: `core/capture` saves screenshots and HTML when errors occur.

## Browser Management

Browsers are managed by `core/browser.BrowserManager`.

-   **Drivers**: Supports Chrome and Firefox.
-   **Pooling**: Optional `WebDriverPool` reuses browser sessions between sites to reduce startup overhead. Enable with `--enable-pooling`.
-   **Chrome Options**:
    -   Production-ready defaults: `--disable-dev-shm-usage`, `--disable-gpu`, `--no-sandbox`.
    -   Automation hiding: `--disable-blink-features=AutomationControlled`.
    -   Security: `acceptInsecureCerts`, `--ignore-certificate-errors`.

## Error Handling & Resilience

### Circuit Breakers
Implemented in `core/circuit_breaker` to prevent cascading failures and overloading target sites.

-   **Scope**: Per-site.
-   **States**: `CLOSED` (Normal), `OPEN` (Failing, requests rejected), `HALF_OPEN` (Testing recovery).
-   **Defaults**:
    -   **Failure Threshold**: 5 consecutive failures triggers `OPEN`.
    -   **Recovery Timeout**: 60 seconds before trying `HALF_OPEN`.
    -   **Success Threshold**: 2 successful requests in `HALF_OPEN` resets to `CLOSED`.

### Artifact Capture
On failure, the system captures:
-   **Screenshot**: PNG image of the browser state.
-   **HTML**: Full page source.
-   **Context**: URL, step name, and timestamp.

## Directory Structure

-   `core/`: Business logic (scraping, browser, auth, metrics).
-   `config/`: Configuration models and validation.
-   `infra/`: Infrastructure concerns (logging, health, signals).
-   `tests/`: Unit, integration, and load tests.
-   `docs/`: Project documentation.
