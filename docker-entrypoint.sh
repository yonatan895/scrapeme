#!/bin/bash
set -e

# Ensure directories exist and are writable
mkdir -p /app/artifacts /app/results

# Check if running as scraper user
if [ "$(id -u)" = "1000" ]; then
  echo "Running as scraper user (UID 1000)"

  # Verify write permissions
  if ! touch /app/results/.test 2>/dev/null; then
    echo "ERROR: Cannot write to /app/results/"
    ls -la /app/
    exit 1
  fi
  rm -f /app/results/.test
fi

# Print startup info
echo "======================================"
echo "Selenium Automation Container"
echo "======================================"
echo "Working directory: $(pwd)"
echo "User: $(whoami) (UID: $(id -u))"
echo "Python: $(python --version)"
echo "Selenium: $(python -c 'import selenium; print(selenium.__version__)')"
echo "======================================"

# Execute the main command
exec python runner.py "$@"
