import pytest
import sys
import os
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config import pg_sql_settings
from auth.models import AdminUser

# Import test data
from test_suite.fixtures.test_data import (
    VALID_USER_DATA, 
    INVALID_USER_DATA, 
    AUTH_TEST_DATA,
    MOCK_USER_RESPONSE
)


@pytest.fixture(scope="session")
def test_app():
    """Create a test FastAPI application."""
    return app


@pytest.fixture(scope="session")
def client(test_app) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application."""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def mock_db_session():
    """Create a mock database session."""
    mock_session = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()
    mock_session.query = Mock()
    mock_session.close = Mock()
    return mock_session


@pytest.fixture(scope="function")
def valid_user_data() -> Dict[str, Any]:
    """Provide valid user data for testing."""
    return VALID_USER_DATA.copy()


@pytest.fixture(scope="function")
def invalid_user_data() -> Dict[str, Dict[str, Any]]:
    """Provide invalid user data scenarios."""
    return INVALID_USER_DATA.copy()


@pytest.fixture(scope="function")
def auth_test_data() -> Dict[str, Dict[str, Any]]:
    """Provide authentication test data."""
    return AUTH_TEST_DATA.copy()


@pytest.fixture(scope="function")
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    }


@pytest.fixture(scope="function")
def sample_user_response():
    """Sample user response data for testing."""
    return {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "is_active": True
    }


@pytest.fixture(scope="function")
def mock_admin_user():
    """Create a mock AdminUser instance."""
    user = Mock(spec=AdminUser)
    user.id = 1
    user.name = "Test User"
    user.email = "test@example.com"
    user.is_active = True
    user.hashed_password = "hashed_password123"
    return user


@pytest.fixture(scope="function")
def mock_db_available():
    """Mock database availability."""
    with patch('auth.api.DB_AVAILABLE', True):
        yield


@pytest.fixture(scope="function")
def mock_db_unavailable():
    """Mock database unavailability."""
    with patch('auth.api.DB_AVAILABLE', False):
        yield


@pytest.fixture(scope="function")
def mock_get_db_session(mock_db_session):
    """Mock the get_db_session dependency."""
    with patch('auth.api.get_db_session') as mock_get_db:
        mock_get_db.return_value = iter([mock_db_session])
        yield mock_get_db


@pytest.fixture(scope="function")
def mock_auth_service():
    """Mock the AdminUserService."""
    with patch('auth.api.AdminUserService') as mock_service:
        yield mock_service
