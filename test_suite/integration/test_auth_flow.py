"""Integration tests for complete authentication flow."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from test_suite.fixtures.test_data import VALID_USER_DATA, AUTH_TEST_DATA


@pytest.mark.integration
@pytest.mark.auth
class TestAuthenticationFlow:
    """Test suite for complete authentication workflows."""

    def test_complete_signup_and_login_flow_demo_mode(self, client: TestClient):
        """Test complete signup and login flow in demo mode."""
        # Step 1: Create a new user
        signup_response = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        
        assert signup_response.status_code == 200
        user_data = signup_response.json()
        assert user_data["email"] == VALID_USER_DATA["email"]
        assert user_data["name"] == VALID_USER_DATA["name"]
        assert user_data["is_active"] is True
        
        # Step 2: Login with the created user
        login_data = {
            "email": VALID_USER_DATA["email"],
            "password": VALID_USER_DATA["password"]
        }
        
        login_response = client.post(
            "/admin-users/authenticate",
            data=login_data
        )
        
        assert login_response.status_code == 200
        auth_data = login_response.json()
        assert auth_data["email"] == VALID_USER_DATA["email"]
        assert auth_data["is_active"] is True

    def test_signup_with_existing_email_demo_mode(self, client: TestClient):
        """Test signup with existing email in demo mode."""
        # First signup - should succeed in demo mode
        response1 = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        assert response1.status_code == 200
        
        # Second signup with same email - should also succeed in demo mode
        # (since demo mode doesn't actually store users)
        response2 = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        assert response2.status_code == 200

    def test_login_with_invalid_credentials_demo_mode(self, client: TestClient):
        """Test login with invalid credentials in demo mode."""
        # In demo mode, any credentials should work
        login_data = AUTH_TEST_DATA["invalid_email"]
        
        response = client.post(
            "/admin-users/authenticate",
            data=login_data
        )
        
        # Demo mode should accept any credentials
        assert response.status_code == 200

    def test_user_creation_and_retrieval_demo_mode(self, client: TestClient):
        """Test user creation and subsequent retrieval in demo mode."""
        # Create user
        create_response = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        assert create_response.status_code == 200
        
        # Try to get user by ID (should return demo user)
        user_id = 1
        get_response = client.get(f"/admin-users/{user_id}")
        assert get_response.status_code == 200
        
        user_data = get_response.json()
        assert user_data["id"] == user_id
        assert user_data["name"] == "Demo User"
        assert user_data["email"] == "demo@example.com"

    def test_get_all_users_demo_mode(self, client: TestClient):
        """Test getting all users in demo mode."""
        # Create a user first
        client.post("/admin-users/", data=VALID_USER_DATA)
        
        # Get all users (should return empty list in demo mode)
        response = client.get("/admin-users/")
        assert response.status_code == 200
        
        users = response.json()
        assert isinstance(users, list)
        assert len(users) == 0  # Demo mode returns empty list

    def test_pagination_parameters(self, client: TestClient):
        """Test user list with pagination parameters."""
        response = client.get("/admin-users/?skip=0&limit=5")
        assert response.status_code == 200
        
        users = response.json()
        assert isinstance(users, list)

    def test_user_retrieval_nonexistent_id_demo_mode(self, client: TestClient):
        """Test retrieving non-existent user by ID in demo mode."""
        user_id = 999
        response = client.get(f"/admin-users/{user_id}")
        
        # Demo mode should return a demo user for any ID
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["id"] == user_id
        assert user_data["name"] == "Demo User"

    @patch('auth.api.DB_AVAILABLE', True)
    @patch('auth.api.AdminUserService.get_user_by_email')
    @patch('auth.api.AdminUserService.create')
    @patch('auth.api.AdminUserService.get_by_id')
    def test_complete_flow_with_database(
        self,
        mock_get_by_id,
        mock_create,
        mock_get_user_by_email,
        mock_get_db_session,
        client: TestClient,
        mock_admin_user
    ):
        """Test complete authentication flow with database available."""
        # Setup mocks
        mock_get_user_by_email.return_value = None  # No existing user
        mock_create.return_value = mock_admin_user
        mock_get_by_id.return_value = mock_admin_user
        
        # Create user
        create_response = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        assert create_response.status_code == 200
        
        # Verify service methods were called
        mock_get_user_by_email.assert_called()
        mock_create.assert_called()
        
        # Get user by ID
        user_id = 1
        get_response = client.get(f"/admin-users/{user_id}")
        assert get_response.status_code == 200
        mock_get_by_id.assert_called_with(mock_get_db_session.return_value.__next__(), model_id=user_id)

    def test_invalid_form_data_handling(self, client: TestClient):
        """Test handling of various invalid form data."""
        invalid_data_sets = [
            {},  # Empty data
            {"name": "Test"},  # Missing email and password
            {"email": "test@example.com"},  # Missing name and password
            {"password": "password123"},  # Missing name and email
            {"name": "", "email": "test@example.com", "password": "pass"},  # Empty name
        ]
        
        for invalid_data in invalid_data_sets:
            response = client.post("/admin-users/", data=invalid_data)
            assert response.status_code == 422  # Validation error

    def test_content_type_handling(self, client: TestClient):
        """Test different content types for form submission."""
        # Test with form data (application/x-www-form-urlencoded)
        response = client.post(
            "/admin-users/",
            data=VALID_USER_DATA
        )
        assert response.status_code == 200

    def test_response_headers(self, client: TestClient):
        """Test response headers for API endpoints."""
        response = client.post("/admin-users/", data=VALID_USER_DATA)
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers in responses."""
        response = client.post("/admin-users/", data=VALID_USER_DATA)
        
        # CORS headers should be present due to middleware
        assert "access-control-allow-origin" in response.headers

    def test_api_error_handling(self, client: TestClient):
        """Test API error handling and response format."""
        # Test with invalid email format
        invalid_data = {
            "name": "Test User",
            "email": "invalid-email",
            "password": "password123"
        }
        
        response = client.post("/admin-users/", data=invalid_data)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
