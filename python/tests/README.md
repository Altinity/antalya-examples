# Docker Test Framework

Tests for the Antalya docker compose examples. They run against the 
setups in the docker and kubernetes directories. 

## Prerequisites

Install dependencies:
```bash
pip install -r ../requirements.txt
pip install -r test-requirements.txt
```

If you are testing against Kubernetes, forward ClickHouse and Ice Rest Catalog
ports to localhost. 
```
kubectl port-forward pod/chi-vector-example-0-0-0 9000 8123 &
kubectl port-forward pod/ice-rest-catalog-0 5000 &
```

## Running Tests

Run the test suite from the python/tests directory:

**Standard mode (uses existing setup):**
```bash
./run.sh
```

**With a specific profile:**
```bash
./run.sh --profile=kubernetes
```

**Manage Docker Compose (starts/stops services):**
```bash
./run.sh --manage-docker
```

**Direct Python execution:**
```bash
# Run all tests
python test.py

# Run with a specific profile
TEST_PROFILE=kubernetes python test.py

# Run a single test
python -m unittest test.AntalyaTestFramework.test_load_ice_and_select -v
```

## Configuration Profiles

Test configuration is managed via `test_profiles.yaml`. Available profiles:

- `docker` (default): Local Docker Compose setup
- `kubernetes`: Kubernetes cluster setup

Profiles define connection settings for:
- Database host, port, user, password
- REST server host and port

## How it works

- `setUpClass()`: Verifies Docker services are running (or starts them if `--manage-docker` is used)
- `tearDownClass()`: Captures container logs and runs `docker compose down` (only if services were started by the framework)
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

Create additional test classes that inherit from `AntalyaTestFramework`
to add more test cases. The Docker Compose services will be managed
automatically.
