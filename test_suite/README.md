# Test Suite for FastAPI Application

This directory contains comprehensive tests for the FastAPI application with authentication.

## Structure

```
test_suite/
├── unit/                 # Unit tests for individual modules
│   ├── test_auth_api.py     # Auth API endpoint tests
│   ├── test_auth_services.py # Auth service layer tests
│   ├── test_auth_schemas.py  # Pydantic schema tests
│   ├── test_frontend_api.py  # Frontend API tests
│   └── test_config.py       # Configuration tests
├── integration/          # Integration tests
│   ├── test_auth_flow.py    # Full authentication flow tests
│   ├── test_api_endpoints.py # All API endpoints integration
│   └── test_database.py     # Database integration tests
├── fixtures/             # Test data and fixtures
│   ├── conftest.py         # Pytest fixtures
│   ├── test_data.py        # Test data constants
│   └── mock_responses.py   # Mock API responses
├── conftest.py           # Main pytest configuration
├── pytest.ini           # Pytest configuration
└── requirements.txt      # Test-specific requirements
```

## Running Tests

### Install test dependencies
```bash
pip install -r test_suite/requirements.txt
```

### Run all tests
```bash
pytest test_suite/
```

### Run specific test categories
```bash
# Unit tests only
pytest test_suite/unit/

# Integration tests only
pytest test_suite/integration/

# Specific test file
pytest test_suite/unit/test_auth_api.py

# Run with coverage
pytest test_suite/ --cov=. --cov-report=html
```

### Run tests with different verbosity
```bash
# Verbose output
pytest test_suite/ -v

# Very verbose output
pytest test_suite/ -vv

# Show local variables in tracebacks
pytest test_suite/ -l
```

## Test Categories

- **Unit Tests**: Test individual functions, classes, and modules in isolation
- **Integration Tests**: Test the interaction between multiple components
- **Mock Tests**: Test behavior with mocked external dependencies (database, APIs)

## Coverage Goals

- Minimum 80% code coverage
- 100% coverage for critical authentication flows
- All API endpoints should have comprehensive tests
