"""Pytest fixtures for test data and mocks."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from .test_data import (
    VALID_USER_DATA, 
    INVALID_USER_DATA, 
    AUTH_TEST_DATA,
    MOCK_USER_RESPONSE,
    generate_user_data
)
from .mock_responses import (
    MOCK_USER_CREATED,
    MOCK_USER_AUTHENTICATED,
    MOCK_USER_EXISTS,
    MOCK_INVALID_CREDENTIALS
)


@pytest.fixture
def valid_user_data() -> Dict[str, Any]:
    """Provide valid user data for testing."""
    return VALID_USER_DATA.copy()


@pytest.fixture
def invalid_user_data() -> Dict[str, Dict[str, Any]]:
    """Provide invalid user data scenarios."""
    return INVALID_USER_DATA.copy()


@pytest.fixture
def auth_test_data() -> Dict[str, Dict[str, Any]]:
    """Provide authentication test data."""
    return AUTH_TEST_DATA.copy()


@pytest.fixture
def random_user_data() -> Dict[str, Any]:
    """Generate random user data for testing."""
    return generate_user_data()


@pytest.fixture
def mock_user_response() -> Dict[str, Any]:
    """Provide mock user response data."""
    return MOCK_USER_RESPONSE.copy()


@pytest.fixture
def mock_successful_creation():
    """Mock successful user creation response."""
    return MOCK_USER_CREATED


@pytest.fixture
def mock_successful_auth():
    """Mock successful authentication response."""
    return MOCK_USER_AUTHENTICATED


@pytest.fixture
def mock_user_exists_error():
    """Mock user already exists error."""
    return MOCK_USER_EXISTS


@pytest.fixture
def mock_invalid_credentials_error():
    """Mock invalid credentials error."""
    return MOCK_INVALID_CREDENTIALS
