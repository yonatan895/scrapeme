# ScrapeMe - Production-Grade Selenium Automation Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A robust, production-ready web scraping and automation framework built with Selenium, featuring comprehensive observability, fault tolerance, and enterprise-grade infrastructure support.

## ✨ Features

### Core Capabilities
- **Multi-site scraping** with YAML-based configuration
- **Authentication flows** with credential management
- **Data extraction** using XPath selectors
- **Screenshot and HTML capture** for debugging
- **Concurrent processing** with configurable thread pools

### Reliability & Resilience
- **Circuit breaker pattern** for fault tolerance
- **Rate limiting** and retry mechanisms
- **Graceful error handling** with context preservation
- **Browser session pooling** for performance
- **Smart waits** and timeout management

### Observability
- **Prometheus metrics** export
- **Structured logging** with correlation IDs
- **Health checks** and readiness probes
- **Grafana dashboards** for monitoring
- **Alert management** with Alertmanager

### Enterprise Features
- **Docker containerization** with multi-stage builds
- **Kubernetes deployment** manifests
- **Selenium Grid** integration
- **HashiCorp Vault** secret management
- **CI/CD pipeline** with GitHub Actions

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Google Chrome or Firefox browser

### Installation

```bash
# Clone the repository
git clone https://github.com/yonatan895/scrapeme.git
cd scrapeme

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Basic Usage

```bash
# Run with default configuration
python runner.py --config config/sites.yaml

# Run in headless mode with custom output
python runner.py --config config/sites.yaml --headless --out results.json

# Run with specific browser and parallel processing
python runner.py --config config/sites.yaml --browser firefox --max-workers 8
```

## 📋 Configuration

### Site Configuration

Define your scraping targets in YAML format:

```yaml
sites:
  - name: example_site
    base_url: "https://example.com"
    wait_timeout_sec: 30
    page_load_timeout_sec: 60
    
    # Optional authentication
    login:
      url: "/login"
      username_field: "//input[@name='username']"
      password_field: "//input[@name='password']"
      submit_button: "//button[@type='submit']"
      success_xpath: "//div[@class='dashboard']"
    
    steps:
      - name: extract_data
        goto_url: "/data"
        wait_xpath: "//div[@class='content']"
        
        fields:
          - name: title
            xpath: "//h1"
          
          - name: items
            xpath: "//div[@class='item']//span"
            multiple: true
          
          - name: timestamp
            xpath: "//time/@datetime"
            attribute: true
```

### Environment Variables

```bash
# Site credentials
EXAMPLE_USERNAME=your_username
EXAMPLE_PASSWORD=your_password

# Optional: Selenium Grid
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub

# Optional: Vault integration
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=your_vault_token

# Optional: Monitoring
METRICS_PORT=9090
LOG_LEVEL=INFO
```

## 🏗️ Architecture

### Core Components

```
├── core/                   # Core framework modules
│   ├── auth.py            # Authentication flows
│   ├── browser.py         # Browser management
│   ├── capture.py         # Screenshot/HTML capture
│   ├── circuit_breaker.py # Circuit breaker implementation
│   ├── metrics.py         # Prometheus metrics
│   ├── rate_limiter.py    # Rate limiting
│   ├── retry.py           # Retry mechanisms
│   ├── scraper.py         # Main scraping logic
│   └── waits.py           # Smart wait strategies
├── config/                # Configuration management
│   ├── loader.py          # YAML config loader
│   ├── models.py          # Configuration models
│   └── validators.py      # Input validation
├── infra/                 # Infrastructure components
│   ├── health.py          # Health check endpoints
│   ├── logging_config.py   # Structured logging setup
│   └── signals.py         # Signal handling
└── runner.py              # Main application entry point
```

### Data Flow

1. **Configuration Loading**: YAML configs are parsed and validated
2. **Browser Initialization**: Selenium drivers are configured and pooled
3. **Authentication**: Optional login flows are executed
4. **Data Extraction**: XPath selectors extract structured data
5. **Error Handling**: Circuit breakers and retries manage failures
6. **Result Serialization**: Data is exported as JSON with metadata

## 🐳 Docker Deployment

### Development

```bash
# Build and run locally
docker build -t scrapeme:dev .
docker run -v $(pwd)/config:/app/config scrapeme:dev
```

### Production with Selenium Grid

```bash
# Deploy full stack with monitoring
docker-compose -f docker-compose.production.yaml up -d

# Scale Chrome nodes
docker-compose -f docker-compose.production.yaml up -d --scale chrome-1=3
```

Services included:
- **selenium-automation**: Main application
- **selenium-hub**: Selenium Grid hub
- **chrome-1/chrome-2**: Chrome browser nodes
- **prometheus**: Metrics collection
- **grafana**: Visualization dashboards
- **alertmanager**: Alert routing

## ☸️ Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=selenium-automation

# View logs
kubectl logs -f deployment/selenium-automation
```

## 📊 Monitoring

### Metrics

The application exports Prometheus metrics on `/metrics`:

- `scrape_requests_total`: Total scraping requests
- `scrape_duration_seconds`: Request duration histogram
- `scrape_errors_total`: Error count by type
- `circuit_breaker_state`: Circuit breaker status
- `browser_pool_size`: Active browser sessions

### Dashboards

Grafana dashboards are provided for:
- **Overview**: Success rates, response times, error distribution
- **Performance**: Throughput, latency, resource utilization
- **Reliability**: Circuit breaker states, retry patterns

### Health Checks

- `GET /health/live`: Liveness probe
- `GET /health/ready`: Readiness probe
- `GET /metrics`: Prometheus metrics endpoint

## 🧪 Testing

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=config --cov=infra

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m e2e          # End-to-end tests

# Run load tests
pytest -m load
```

### Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests with external dependencies
├── e2e/              # End-to-end workflow tests
├── fixtures/         # Test data and mock configurations
└── conftest.py       # Pytest configuration and fixtures
```

## 🔧 Development

### Setup Development Environment

```bash
# Install pre-commit hooks
pre-commit install

# Run code formatting
make format

# Run linting
make lint

# Run security checks
make security

# Run all quality checks
make check
```

### Code Quality Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **pylint**: Static analysis
- **bandit**: Security scanning
- **safety**: Dependency vulnerability scanning

### Makefile Commands

```bash
make help           # Show available commands
make install        # Install dependencies
make test          # Run test suite
make format        # Format code
make lint          # Run linters
make security      # Security checks
make build         # Build Docker image
make deploy        # Deploy to production
```

## 🔒 Security

### Credential Management

- **Environment Variables**: Local development
- **HashiCorp Vault**: Production secrets
- **Kubernetes Secrets**: Container orchestration
- **Docker Secrets**: Docker Swarm deployment

### Security Best Practices

- Non-root container execution
- Minimal base images with security scanning
- Dependency vulnerability monitoring
- Secure secret injection
- Network policy enforcement

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run quality checks: `make check`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests
- Update documentation for new features
- Ensure backwards compatibility

## 📚 API Reference

### Core Classes

#### `SiteScraper`
Main scraping orchestrator.

```python
from core.scraper import SiteScraper

scraper = SiteScraper(site_config, waiter, logger)
data = scraper.run()
```

#### `BrowserManager`
Manages browser lifecycle and pooling.

```python
from core.browser import BrowserManager

manager = BrowserManager(browser='chrome', headless=True)
with manager.session() as driver:
    driver.get('https://example.com')
```

#### `AuthFlow`
Handles authentication workflows.

```python
from core.auth import AuthFlow

auth = AuthFlow(waiter, logger, secrets)
auth.login(login_config, site_name='example')
```

## 🔗 Related Projects

- [Selenium WebDriver](https://selenium-python.readthedocs.io/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Structlog](https://www.structlog.org/)
- [Tenacity](https://tenacity.readthedocs.io/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yonatan895/scrapeme/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yonatan895/scrapeme/discussions)
- **Email**: yonatan.leshco@gmail.com

## 🗺️ Roadmap

- [ ] Async/await support for improved concurrency
- [ ] Plugin system for custom extractors
- [ ] Machine learning-based element detection
- [ ] Real-time streaming data processing
- [ ] Multi-cloud deployment templates
- [ ] Advanced anti-bot detection evasion
- [ ] GraphQL API for configuration management

---

**Built with ❤️ by [Yonatan Cohen](https://github.com/yonatan895)**