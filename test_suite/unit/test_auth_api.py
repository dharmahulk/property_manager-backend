"""Unit tests for authentication API endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from test_suite.fixtures.test_data import VALID_USER_DATA, INVALID_USER_DATA


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.api
class TestAuthAPI:
    """Test suite for authentication API endpoints."""

    def test_create_user_success_demo_mode(self, client: TestClient, mock_db_unavailable):
        """Test successful user creation in demo mode."""
        response = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == VALID_USER_DATA["name"]
        assert data["email"] == VALID_USER_DATA["email"]
        assert data["is_active"] is True
        assert "id" in data

    def test_create_user_missing_name(self, client: TestClient):
        """Test user creation with missing name field."""
        response = client.post(
            "/admin-users/",
            data=INVALID_USER_DATA["missing_name"]
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(error["loc"] == ["body", "name"] for error in error_detail)

    def test_create_user_missing_email(self, client: TestClient):
        """Test user creation with missing email field."""
        response = client.post(
            "/admin-users/",
            data=INVALID_USER_DATA["missing_email"]
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(error["loc"] == ["body", "email"] for error in error_detail)

    def test_create_user_missing_password(self, client: TestClient):
        """Test user creation with missing password field."""
        response = client.post(
            "/admin-users/",
            data=INVALID_USER_DATA["missing_password"]
        )
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(error["loc"] == ["body", "password"] for error in error_detail)

    def test_create_user_invalid_email(self, client: TestClient):
        """Test user creation with invalid email format."""
        response = client.post(
            "/admin-users/",
            data=INVALID_USER_DATA["invalid_email"]
        )
        
        assert response.status_code == 422

    def test_create_user_empty_name(self, client: TestClient):
        """Test user creation with empty name."""
        response = client.post(
            "/admin-users/",
            data=INVALID_USER_DATA["empty_name"]
        )
        
        # Should pass validation but might fail business logic
        # This depends on your specific validation requirements
        assert response.status_code in [200, 422]

    @patch('auth.api.DB_AVAILABLE', True)
    @patch('auth.api.AdminUserService.get_user_by_email')
    @patch('auth.api.AdminUserService.create')
    def test_create_user_success_with_db(
        self, 
        mock_create, 
        mock_get_user, 
        mock_get_db_session,
        client: TestClient,
        mock_admin_user
    ):
        """Test successful user creation with database available."""
        # Mock no existing user
        mock_get_user.return_value = None
        # Mock successful creation
        mock_create.return_value = mock_admin_user
        
        response = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        
        assert response.status_code == 200
        mock_get_user.assert_called_once()
        mock_create.assert_called_once()

    @patch('auth.api.DB_AVAILABLE', True)
    @patch('auth.api.AdminUserService.get_user_by_email')
    def test_create_user_email_already_exists(
        self, 
        mock_get_user, 
        mock_get_db_session,
        client: TestClient,
        mock_admin_user
    ):
        """Test user creation when email already exists."""
        # Mock existing user
        mock_get_user.return_value = mock_admin_user
        
        response = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_authenticate_user_demo_mode(self, client: TestClient, mock_db_unavailable):
        """Test user authentication in demo mode."""
        auth_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post(
            "/admin-users/authenticate",
            data=auth_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == auth_data["email"]
        assert data["is_active"] is True

    @patch('auth.api.DB_AVAILABLE', True)
    @patch('auth.api.AdminUserService.get_user_by_email')
    @patch('auth.api.AdminUserResponse.validate_password')
    def test_authenticate_user_success_with_db(
        self,
        mock_validate_password,
        mock_get_user,
        mock_get_db_session,
        client: TestClient,
        mock_admin_user
    ):
        """Test successful authentication with database."""
        # Mock user exists and password is valid
        mock_get_user.return_value = mock_admin_user
        mock_validate_password.return_value = True
        
        auth_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post(
            "/admin-users/authenticate",
            data=auth_data
        )
        
        assert response.status_code == 200

    @patch('auth.api.DB_AVAILABLE', True)
    @patch('auth.api.AdminUserService.get_user_by_email')
    def test_authenticate_user_not_found(
        self,
        mock_get_user,
        mock_get_db_session,
        client: TestClient
    ):
        """Test authentication with non-existent user."""
        # Mock user not found
        mock_get_user.return_value = None
        
        auth_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post(
            "/admin-users/authenticate",
            data=auth_data
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_read_users_demo_mode(self, client: TestClient, mock_db_unavailable):
        """Test reading users list in demo mode."""
        response = client.get("/admin-users/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_read_user_by_id_demo_mode(self, client: TestClient, mock_db_unavailable):
        """Test reading user by ID in demo mode."""
        user_id = 1
        response = client.get(f"/admin-users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == "Demo User"
        assert data["email"] == "demo@example.com"
        assert data["is_active"] is True

    @patch('auth.api.DB_AVAILABLE', True)
    @patch('auth.api.AdminUserService.get_by_id')
    def test_read_user_by_id_not_found(
        self,
        mock_get_by_id,
        mock_get_db_session,
        client: TestClient
    ):
        """Test reading non-existent user by ID."""
        # Mock user not found
        mock_get_by_id.return_value = None
        
        user_id = 999
        response = client.get(f"/admin-users/{user_id}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
