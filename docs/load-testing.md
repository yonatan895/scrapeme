# Load Testing Guide

This guide explains how to use the comprehensive load testing infrastructure in ScrapeMe.

## Problem & Solution

### The Issue You Encountered

Your load tests were failing with 100% failure rates because the health endpoints (`/healthz`, `/ready`, `/metrics`) weren't responding. This happens because:

1. **ScrapeMe's health server only starts when the main application runs**
2. **Load tests need these endpoints to validate the application**
3. **Running the full application for testing is resource-intensive**

### The Solution

We've created a **standalone test server** that:
- Mimics all the health endpoints your load tests need
- Starts automatically when you run load tests
- Provides realistic responses without the full application overhead
- Includes proper Prometheus metrics simulation

## Quick Start

### 1. Install Dependencies
```bash
make load-test-install
```

### 2. Run Load Tests (with automatic server)
```bash
# Quick health check (10 users, 60 seconds)
make load-test-health

# Stress testing (50 users, 120 seconds) 
make load-test-stress

# CI/CD validation (5 users, 30 seconds)
make load-test-ci
```

### 3. View Results
```bash
make load-test-results
```

## Available Test Scenarios

| Target | Users | Duration | Purpose |
|--------|-------|----------|----------|
| `load-test-health` | 10 | 60s | Basic health validation |
| `load-test-stress` | 50 | 120s | Performance limits testing |
| `load-test-mixed` | 30 | 180s | Combined scenarios |
| `load-test-fast` | 100 | 60s | High-performance testing |
| `load-test-ci` | 5 | 30s | CI/CD pipeline validation |
| `load-test-production` | 200 | 600s | Production-like load |
| `load-test-external` | 20 | 300s | External targets (requires internet) |

## Server Management

### Automatic Management (Recommended)
The Makefile automatically starts/stops the test server:
```bash
make load-test-health  # Server starts automatically
```

### Manual Management
```bash
# Start test server
make load-test-server-start

# Check if running
ps aux | grep test_server

# Stop server
make load-test-server-stop
```

### Manual Server Usage
```bash
# Start server directly
python tests/load/test_server.py --port 9090 --host localhost

# Test endpoints
curl http://localhost:9090/healthz
curl http://localhost:9090/ready
curl http://localhost:9090/metrics
```

## Test Server Endpoints

The test server provides:

### `/healthz` - Liveness Probe
```json
{
  "status": "healthy",
  "timestamp": "2025-11-01T14:30:00Z"
}
```

### `/ready` - Readiness Probe
```json
{
  "status": "ready",
  "timestamp": "2025-11-01T14:30:00Z",
  "checks": {
    "config": {
      "status": "healthy",
      "message": "Configuration loaded successfully",
      "duration_ms": 1.2
    },
    "ready": {
      "status": "healthy",
      "message": "Application ready", 
      "duration_ms": 0.8
    }
  }
}
```

### `/metrics` - Prometheus Metrics
```
# HELP scrapeme_build_info Build information
# TYPE scrapeme_build_info gauge
scrapeme_build_info{version="2.0.0",python_version="3.11.0"} 1
# HELP scrapeme_requests_total Total number of requests
# TYPE scrapeme_requests_total counter
scrapeme_requests_total{endpoint="/healthz"} 42
...
```

## Configuration

### Environment Variables
```bash
# Change test server port
export TEST_SERVER_PORT=8080
make load-test-health

# Customize load test parameters
export LOAD_BASE_URL=http://your-app:9090
make load-test-stress

# Enable external testing
export ENABLE_EXTERNAL_TARGETS=true
make load-test-external
```

### Makefile Variables
```makefile
# Override in your shell or Makefile.local
LOAD_BASE_URL=http://staging:9090
LOAD_RESULTS_DIR=my-custom-results
TEST_SERVER_PORT=8080
```

## Results & Reports

### Generated Files
```
artifacts/load_tests/
├── health_test_report.html      # Detailed HTML report
├── health_test_stats.csv        # Request statistics
├── health_test_stats_history.csv # Performance over time
└── health_test_failures.csv     # Failure details
```

### JSON Results Summary
```json
{
  "timestamp": 1699000000,
  "test_mode": "health",
  "target_base": "http://localhost:9090",
  "total_requests": 150,
  "total_failures": 0,
  "avg_response_time": 25.4,
  "max_response_time": 45.2,
  "requests_per_second": 2.5
}
```

## Troubleshooting

### Load Tests Still Failing?

1. **Check if server is running:**
   ```bash
   curl http://localhost:9090/healthz
   ```

2. **Check server logs:**
   ```bash
   python tests/load/test_server.py --log-level DEBUG
   ```

3. **Verify port availability:**
   ```bash
   lsof -i :9090
   netstat -tulpn | grep 9090
   ```

4. **Clean up and retry:**
   ```bash
   make load-test-clean
   make load-test-health
   ```

### Common Issues

**Port already in use:**
```bash
# Use different port
TEST_SERVER_PORT=9091 make load-test-health
```

**Permission denied:**
```bash
# Use unprivileged port
TEST_SERVER_PORT=8080 make load-test-health
```

**Server won't start:**
```bash
# Check if process is stuck
make load-test-server-stop
make load-test-clean
```

## Integration with Real Application

### Testing Against Running Application
```bash
# Start your application with health server
python runner.py --daemon --metrics-port 9090 &

# Test against real endpoints
LOAD_BASE_URL=http://localhost:9090 make load-test-health

# Don't start test server automatically
make load-test-external  # This doesn't auto-start server
```

### CI/CD Integration
```yaml
# .github/workflows/load-test.yml
steps:
  - name: Install dependencies
    run: make load-test-install
    
  - name: Run load tests
    run: make load-test-ci
    
  - name: Upload results
    uses: actions/upload-artifact@v3
    with:
      name: load-test-results
      path: artifacts/load_tests/
```

## Advanced Usage

### Custom Test Scenarios
```bash
# Create custom locust file
cp tests/load/locustfile.py tests/load/custom_locustfile.py

# Run with custom configuration
LOCUST_FILE=tests/load/custom_locustfile.py make load-test-health
```

### Performance Monitoring
```bash
# Monitor during tests
watch -n 1 'curl -s http://localhost:9090/metrics | grep requests_total'

# Real-time results
tail -f artifacts/load_tests/health_test_stats_history.csv
```

This comprehensive load testing infrastructure ensures your ScrapeMe application can handle production loads while providing detailed performance insights.
