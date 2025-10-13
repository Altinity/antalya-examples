# Docker Test Framework

Tests for the Antalya docker compose examples. 

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r test-requirements.txt
```

2. (Optional) Install development tools for code formatting:
```bash
pip install black isort flake8
```

## Running Tests

Run the test suite from the docker/tests directory:

**Standard mode (starts/stops Docker Compose):**
```bash
./run.sh
```

**Use existing Docker Compose setup:**
```bash
./run.sh --use-existing
```

**Direct Python execution:**
```bash
python test.py
```

## How it works

- `setUpClass()`: Runs `docker compose up -d` before any tests (unless `--use-existing` is used)
- `tearDownClass()`: Captures container logs and runs `docker compose down` after all tests complete (only if services were started by the framework)
- Container logs are automatically saved to `test_logs/` directory with timestamps for debugging
- The framework includes sample HTTP tests and Python script execution tests
- Tests will pass if the HTTP response matches the expected status code
- The helper function allows specifying a single expected status code for precise validation

## Log Files

Container logs are automatically captured in the `test_logs/` directory:
- Individual service logs: `{service_name}_{timestamp}.log`
- Combined logs: `combined_{timestamp}.log`
- Logs include timestamps and are captured whether tests pass or fail

## Code Formatting

Format code, sort imports, and check style with flake8

```
black . && isort . && flake8 .
```

## Adding More Tests

Create additional test classes that inherit from `DockerTestFramework`
to add more test cases. The Docker Compose services will be managed
automatically.
