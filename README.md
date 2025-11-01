# ScrapeMe - Production-Grade Selenium Automation Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A robust, production-ready web scraping and automation framework built with Selenium, featuring comprehensive observability, fault tolerance, and enterprise-grade infrastructure support.

## ✨ Features

### Core Capabilities
- **Multi-site scraping** with YAML-based configuration
- **Authentication flows** with credential management (environment variables and HashiCorp Vault)
- **Data extraction** using XPath selectors with multiple field support
- **Screenshot and HTML capture** for debugging and artifact collection
- **Concurrent processing** with configurable thread pools
- **Frame handling** for complex web applications

### Reliability & Resilience
- **Circuit breaker pattern** for fault tolerance with configurable thresholds
- **Rate limiting** with token bucket algorithm
- **Retry mechanisms** with exponential backoff using Tenacity
- **Graceful error handling** with rich context preservation
- **Browser session pooling** for performance optimization
- **Smart wait strategies** with custom waiter implementations

### Observability
- **Prometheus metrics** export on configurable port (default 9090)
- **Structured logging** with JSON output support
- **Health check endpoints** (liveness/readiness probes)
- **Build info metrics** with version tracking
- **Performance metrics** (success rates, duration histograms, error counts)

### Enterprise Features
- **Docker containerization** with multi-stage builds (production/development/test)
- **Kubernetes deployment** with HPA, ServiceMonitor, and PVC
- **Selenium Grid** integration for horizontal scaling
- **HashiCorp Vault** integration for secure secret management
- **GitHub Actions CI/CD** with comprehensive quality gates
- **UV package manager** support for fast dependency management

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (3.12 recommended)
- [UV package manager](https://github.com/astral-sh/uv) (recommended) or pip
- Google Chrome or Firefox browser
- Docker (optional, for containerized deployment)

### Installation

#### Option 1: Using UV (Recommended)

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# or: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Clone and setup
git clone https://github.com/yonatan895/scrapeme.git
cd scrapeme

# Complete setup (creates venv, installs all dependencies)
make quickstart

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows
```

#### Option 2: Using pip

```bash
git clone https://github.com/yonatan895/scrapeme.git
cd scrapeme

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[all]"
```

### Basic Usage

```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run with example configuration
python runner.py --config config/sites.yaml --headless

# Run with custom output and parallel processing
python runner.py --config config/sites.yaml \
    --headless \
    --out results.json \
    --max-workers 4 \
    --artifact-dir ./artifacts

# Run with Selenium Grid
python runner.py --config config/sites.yaml \
    --remote-url http://localhost:4444/wd/hub \
    --headless
```

## 📋 Configuration

### Site Configuration Format

Define your scraping targets in YAML format:

```yaml
sites:
  - name: example_site
    base_url: "https://example.com"
    wait_timeout_sec: 30        # Element wait timeout
    page_load_timeout_sec: 60   # Page load timeout
    
    # Optional authentication
    login:
      url: "/login"
      username_field: "//input[@name='username']"
      password_field: "//input[@name='password']"
      submit_button: "//button[@type='submit']"
      success_xpath: "//div[@class='dashboard']"
      # Credentials come from environment variables:
      # EXAMPLE_SITE_USERNAME and EXAMPLE_SITE_PASSWORD
    
    steps:
      - name: extract_data
        goto_url: "/data"
        wait_xpath: "//div[@class='content']"  # Wait for this element
        
        fields:
          - name: title
            xpath: "//h1"
            # Single text extraction
          
          - name: items
            xpath: "//div[@class='item']//span"
            multiple: true  # Extract multiple elements
          
          - name: timestamp
            xpath: "//time/@datetime"
            attribute: true  # Extract attribute value
            
          - name: links
            xpath: "//a/@href"
            multiple: true
            attribute: true
```

### Environment Variables

```bash
# Site credentials (format: {SITE_NAME_UPPER}_USERNAME/PASSWORD)
EXAMPLE_SITE_USERNAME=your_username
EXAMPLE_SITE_PASSWORD=your_password

# Additional sites
QUOTES_TO_SCRAPE_USERNAME=user1
QUOTES_TO_SCRAPE_PASSWORD=pass1

# Optional: Selenium Grid
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub

# Optional: Vault integration
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=your_vault_token

# Optional: Custom Chrome binary
CHROME_BINARY_PATH=/usr/bin/google-chrome

# Optional: Monitoring
METRICS_PORT=9090
LOG_LEVEL=INFO
```

### Command Line Options

```bash
python runner.py --help

# Key options:
--config PATH              # Configuration file (required)
--browser chrome|firefox   # Browser choice (default: chrome)
--headless                 # Run in headless mode
--incognito               # Use incognito/private mode
--remote-url URL          # Selenium Grid URL
--max-workers N           # Concurrent processing (default: 4)
--artifact-dir PATH       # Screenshot/HTML capture directory
--no-artifacts           # Disable artifact capture
--enable-pooling         # Enable browser session pooling
--metrics-port PORT      # Prometheus metrics port (default: 9090)
--json-logs              # Enable JSON log format
--log-level LEVEL        # Logging level
--out PATH               # Output file (default: results.json)
```

## 🏗️ Architecture

### Project Structure

```
├── core/                   # Core framework modules
│   ├── auth.py            # Authentication flows with Vault support
│   ├── browser.py         # Browser management and pooling
│   ├── capture.py         # Screenshot/HTML artifact capture
│   ├── circuit_breaker.py # Circuit breaker with state management
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── frames.py          # Frame handling for complex sites
│   ├── metrics.py         # Prometheus metrics collection
│   ├── rate_limiter.py    # Token bucket rate limiting
│   ├── retry.py           # Retry logic with backoff strategies
│   ├── scraper.py         # Main scraping orchestration
│   ├── secrets.py         # Secret management (env vars + Vault)
│   ├── serialization.py   # JSON serialization utilities
│   ├── type_aliases.py    # Type definitions
│   ├── url.py             # URL manipulation utilities
│   └── waits.py           # Smart wait strategies
├── config/                # Configuration management
│   ├── loader.py          # YAML configuration loader
│   ├── models.py          # Pydantic configuration models
│   ├── sites.yaml         # Example site configuration
│   └── validators.py      # Input validation
├── infra/                 # Infrastructure components
│   ├── health.py          # Health check registry
│   ├── logging_config.py  # Structured logging setup
│   └── signals.py         # Graceful shutdown handling
├── tests/                 # Comprehensive test suite
│   ├── unit/              # Unit tests (planned)
│   ├── benchmarks/        # Performance benchmarks
│   ├── chaos/             # Chaos engineering tests
│   ├── load/              # Load testing
│   ├── property/          # Property-based testing
│   └── conftest.py        # Pytest configuration
├── monitoring/            # Observability stack
│   ├── prometheus.yaml    # Prometheus configuration
│   ├── alerts.yaml        # Alert rules
│   ├── alertmanager.yaml  # Alert routing
│   └── grafana/           # Dashboard configurations
├── k8s/                   # Kubernetes manifests
├── .github/workflows/     # CI/CD pipelines
└── runner.py              # Main application entry point
```

### Data Flow

1. **Configuration Loading**: YAML configs parsed with Pydantic validation
2. **Browser Management**: WebDriver instances created with pooling support
3. **Authentication**: Optional login flows using stored credentials
4. **Data Extraction**: XPath-based field extraction with error handling
5. **Artifact Capture**: Screenshots and HTML saved on errors
6. **Circuit Breaking**: Failed sites are temporarily disabled
7. **Result Serialization**: Structured JSON output with metadata
8. **Metrics Export**: Performance data exported to Prometheus

## 🐳 Docker Deployment

### Development

```bash
# Build development image
make docker-build-dev

# Run with mounted configuration
make docker-run
```

### Production with Full Stack

```bash
# Deploy complete monitoring stack
make compose-up

# Services available at:
# - Selenium Hub: http://localhost:4444
# - Prometheus: http://localhost:9091  
# - Grafana: http://localhost:3000 (admin/admin)
# - Alertmanager: http://localhost:9093

# Scale Chrome nodes
docker-compose -f docker-compose.production.yaml up -d --scale chrome-1=3

# View logs
make compose-logs

# Stop stack
make compose-down
```

### Multi-stage Docker Build

The Dockerfile supports multiple targets:
- **development**: With dev tools and debugging
- **test**: For running test suite
- **production**: Minimal runtime image

## ⚙️ Kubernetes Deployment

```bash
# Deploy to Kubernetes
make k8s-deploy

# Check deployment status
make k8s-status

# View logs
make k8s-logs

# Port forward metrics
make k8s-port-forward

# Delete deployment
make k8s-delete
```

Kubernetes features:
- **HPA (Horizontal Pod Autoscaling)** based on CPU/memory
- **ServiceMonitor** for Prometheus scraping
- **PVC (Persistent Volume Claims)** for artifacts
- **ConfigMaps** for configuration
- **Secrets** for credentials

## 📊 Monitoring

### Prometheus Metrics

Exported on `/metrics` endpoint (default port 9090):

```
# Success/failure rates
scrape_requests_total{site="example", status="success|failure"}

# Response time distribution
scrape_duration_seconds{site="example"}

# Error tracking
scrape_errors_total{site="example", error_type="timeout|automation|circuit_breaker"}

# Circuit breaker states
circuit_breaker_state{site="example", state="closed|open|half_open"}

# Browser pool metrics
browser_pool_active_sessions
browser_pool_total_sessions

# Build information
build_info{version="2.0.0", python_version="3.11.x"}
```

### Health Endpoints

- `GET /health/live`: Liveness probe (always returns 200)
- `GET /health/ready`: Readiness probe (checks dependencies)
- `GET /metrics`: Prometheus metrics

### Alerting Rules

Pre-configured alerts in `monitoring/alerts.yaml`:
- High error rate (>10% for 5 minutes)
- Circuit breaker open
- Response time degradation
- Application down

## 🧪 Testing

### Quick Testing

```bash
# Quick setup verification
make check

# Run all tests with coverage
make test

# Run specific test categories
make test-unit          # Unit tests
make test-integration   # Integration tests  
make test-benchmarks    # Performance tests
make test-property      # Property-based tests
```

### Comprehensive Testing

```bash
# Install all test dependencies
make install-all

# Run full test suite
make test-all

# Run tests in parallel (faster)
make test-parallel

# Run only failed tests
make test-failed

# Watch mode (auto-rerun on changes)
make test-watch
```

### Test Categories

- **Unit tests**: Fast, isolated component testing
- **Integration tests**: Database and external service integration
- **End-to-end tests**: Full workflow testing with real browsers
- **Property tests**: Hypothesis-based testing for edge cases
- **Load tests**: Performance and scalability testing
- **Chaos tests**: Fault injection and resilience testing
- **Benchmarks**: Performance regression testing

## 🛠️ Development

### Setup Development Environment

```bash
# Complete setup with all tools
make quickstart

# Or manual setup
make venv install-all verify-install

# Install pre-commit hooks
make pre-commit-install
```

### Development Workflow

```bash
# Before committing
make check              # Format, lint, and quick tests

# Individual commands
make format            # Auto-format with Black and isort
make lint              # Run all linters (mypy, pylint, etc.)
make security-check    # Bandit and Safety scans
make type-check        # Detailed mypy analysis

# Full CI pipeline locally
make ci-local
```

### Code Quality Tools

- **Black** (100 chars): Code formatting
- **isort**: Import organization
- **mypy**: Static type checking with strict mode
- **pylint**: Code quality analysis (8.5+ score required)
- **bandit**: Security vulnerability scanning
- **safety**: Dependency vulnerability checking
- **pre-commit**: Git hooks for quality gates

### Available Make Commands

```bash
make help              # Show all available commands

# Environment
make venv              # Create virtual environment
make install-all       # Install all dependencies
make verify-install    # Verify installation

# Development
make dev               # Setup complete dev environment
make format            # Auto-format code
make lint              # Run all linters
make test              # Run tests with coverage
make check             # Pre-commit validation

# Docker
make docker-build      # Build production image
make docker-test       # Test in container
make compose-up        # Start full stack

# Kubernetes
make k8s-deploy        # Deploy to cluster
make k8s-logs          # View pod logs

# Utilities
make clean             # Clean generated files
make info              # Show project info
make diagnose          # Troubleshoot issues
```

## 🔧 Configuration Examples

### Example Site: Quotes to Scrape

The included example demonstrates scraping [quotes.toscrape.com](http://quotes.toscrape.com/):

```yaml
sites:
  - name: quotes_to_scrape
    base_url: "http://quotes.toscrape.com/"
    wait_timeout_sec: 20
    page_load_timeout_sec: 30
    
    steps:
      - name: extract_quote_1
        goto_url: "/"
        wait_xpath: "//div[@class='quote']"
        fields:
          - name: quote_text
            xpath: "//div[@class='quote'][1]//span[@class='text']"
          - name: author
            xpath: "//div[@class='quote'][1]//small[@class='author']"
          - name: tags
            xpath: "//div[@class='quote'][1]//a[@class='tag']"
            multiple: true
```

### Authentication Example

```yaml
sites:
  - name: secure_site
    base_url: "https://example.com"
    login:
      url: "/login"
      username_field: "//input[@id='username']"
      password_field: "//input[@id='password']"
      submit_button: "//button[@type='submit']"
      success_xpath: "//div[@class='dashboard']"
      # Uses SECURE_SITE_USERNAME and SECURE_SITE_PASSWORD from env
```

## 🚀 API Reference

### Core Classes

#### `SiteScraper`
Main scraping orchestrator with error handling and metrics.

```python
from core.scraper import SiteScraper
from core.waits import Waiter

scraper = SiteScraper(site_config, waiter, logger, artifact_dir)
data = scraper.run()  # Returns extracted data dict
```

#### `BrowserManager`
Manages WebDriver lifecycle with session pooling.

```python
from core.browser import BrowserManager

manager = BrowserManager(
    browser='chrome',
    headless=True,
    enable_pooling=True
)

with manager.session() as driver:
    driver.get('https://example.com')
    # Driver automatically returned to pool
```

#### `AuthFlow`
Handles login workflows with credential management.

```python
from core.auth import AuthFlow
from core.secrets import EnvSecrets

auth = AuthFlow(waiter, logger, EnvSecrets())
auth.login(login_config, site_name='example')
```

#### `CircuitBreaker`
Implements circuit breaker pattern for fault tolerance.

```python
from core.circuit_breaker import CircuitBreakerRegistry

breaker = CircuitBreakerRegistry.get('site_name')
if breaker.is_call_permitted():
    # Execute operation
    breaker.record_success()
else:
    # Circuit is open, skip operation
    pass
```

## 🔍 Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   ```bash
   # Specify custom ChromeDriver path
   python runner.py --chromedriver-path /path/to/chromedriver
   
   # Or use system Chrome binary
   export CHROME_BINARY_PATH=/usr/bin/google-chrome
   ```

2. **Permission Errors in Docker**
   ```bash
   # Ensure proper permissions for mounted volumes
   sudo chown -R $(id -u):$(id -g) results artifacts
   ```

3. **Memory Issues**
   ```bash
   # Reduce concurrent workers
   python runner.py --max-workers 2
   
   # Disable browser pooling
   python runner.py --no-pooling
   ```

4. **Network Timeouts**
   ```yaml
   # Increase timeouts in config
   sites:
     - name: slow_site
       wait_timeout_sec: 60
       page_load_timeout_sec: 120
   ```

### Diagnostic Commands

```bash
# Check environment health
make health-check

# Diagnose common issues
make diagnose

# Verify all tools are working
make verify-install

# Check dependency versions
make deps-tree
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run quality checks: `make ci-local`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Development Guidelines

- Follow PEP 8 and use Black formatting (100 char line length)
- Add comprehensive type hints (mypy strict mode)
- Write tests for new functionality
- Update documentation for user-facing changes
- Maintain backwards compatibility
- Use conventional commit messages

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yonatan895/scrapeme/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yonatan895/scrapeme/discussions)
- **Email**: yonatan.leshco@gmail.com

## 🗺️ Roadmap

### Planned Features
- [ ] Async/await support for improved concurrency
- [ ] Plugin system for custom extractors and processors
- [ ] GraphQL API for configuration management
- [ ] Real-time data streaming with WebSocket support
- [ ] Machine learning-based element detection
- [ ] Advanced anti-bot detection evasion
- [ ] Multi-cloud deployment templates (AWS/GCP/Azure)
- [ ] Built-in data validation and transformation

### Current Focus
- Expanding test coverage to 95%+
- Performance optimization and memory usage reduction
- Enhanced monitoring and alerting capabilities
- Documentation improvements and examples

---

**Built with ❤️ by [Yonatan Cohen](https://github.com/yonatan895)**

*A production-ready framework for reliable web scraping at scale.*