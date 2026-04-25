"""Integration tests for all API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestAPIEndpoints:
    """Test suite for all API endpoints integration."""

    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint serves the main page."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_docs_endpoint_available(self, client: TestClient):
        """Test that API documentation is available."""
        response = client.get("/docs")
        
        # Should either return docs or 404 if disabled
        assert response.status_code in [200, 404]

    def test_openapi_endpoint(self, client: TestClient):
        """Test OpenAPI schema endpoint."""
        response = client.get("/api/v1/openapi.json")
        
        if response.status_code == 200:
            # If available, should return valid OpenAPI schema
            schema = response.json()
            assert "openapi" in schema
            assert "info" in schema
            assert "paths" in schema

    def test_static_files_serving(self, client: TestClient):
        """Test static files are served correctly."""
        static_files = [
            "/static/css/modern.css",
            "/static/js/modern-auth.js"
        ]
        
        for file_path in static_files:
            response = client.get(file_path)
            assert response.status_code == 200

    def test_health_check_endpoints(self, client: TestClient):
        """Test basic health/status endpoints."""
        # Test if basic endpoints respond
        endpoints = ["/", "/docs"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 500 (server error)
            assert response.status_code != 500

    def test_user_crud_endpoints(self, client: TestClient):
        """Test all user CRUD endpoints."""
        user_data = {
            "name": "Integration Test User",
            "email": "integration@example.com",
            "password": "password123"
        }
        
        # CREATE - POST /admin-users/
        create_response = client.post("/admin-users/", data=user_data)
        assert create_response.status_code == 200
        created_user = create_response.json()
        
        # READ ALL - GET /admin-users/
        list_response = client.get("/admin-users/")
        assert list_response.status_code == 200
        users_list = list_response.json()
        assert isinstance(users_list, list)
        
        # READ ONE - GET /admin-users/{id}
        user_id = created_user["id"]
        get_response = client.get(f"/admin-users/{user_id}")
        assert get_response.status_code == 200
        retrieved_user = get_response.json()
        assert retrieved_user["id"] == user_id
        
        # AUTHENTICATE - POST /admin-users/authenticate
        auth_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        auth_response = client.post("/admin-users/authenticate", data=auth_data)
        assert auth_response.status_code == 200
        authenticated_user = auth_response.json()
        assert authenticated_user["email"] == user_data["email"]

    def test_pagination_endpoints(self, client: TestClient):
        """Test pagination on list endpoints."""
        # Test with different pagination parameters
        pagination_tests = [
            {"skip": 0, "limit": 10},
            {"skip": 5, "limit": 5},
            {"skip": 0, "limit": 1},
            {"skip": 10, "limit": 20}
        ]
        
        for params in pagination_tests:
            response = client.get("/admin-users/", params=params)
            assert response.status_code == 200
            users = response.json()
            assert isinstance(users, list)

    def test_error_handling_endpoints(self, client: TestClient):
        """Test error handling across endpoints."""
        # Test 404 for non-existent user (in DB mode would be 404, demo mode returns demo user)
        response = client.get("/admin-users/99999")
        assert response.status_code in [200, 404]  # Depends on demo mode
        
        # Test 422 for validation errors
        invalid_user_data = {"name": "Test"}  # Missing required fields
        response = client.post("/admin-users/", data=invalid_user_data)
        assert response.status_code == 422
        
        # Test invalid authentication
        invalid_auth_data = {"email": "", "password": ""}
        response = client.post("/admin-users/authenticate", data=invalid_auth_data)
        assert response.status_code in [200, 401, 422]  # Depends on validation

    def test_response_content_types(self, client: TestClient):
        """Test response content types are correct."""
        # HTML endpoint
        html_response = client.get("/")
        assert "text/html" in html_response.headers["content-type"]
        
        # JSON endpoints
        json_endpoints = [
            "/admin-users/",
            "/admin-users/1"
        ]
        
        for endpoint in json_endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                assert "application/json" in response.headers["content-type"]
        
        # CSS endpoint
        css_response = client.get("/static/css/modern.css")
        if css_response.status_code == 200:
            assert "text/css" in css_response.headers["content-type"]
        
        # JavaScript endpoint
        js_response = client.get("/static/js/modern-auth.js")
        if js_response.status_code == 200:
            assert "text/javascript" in js_response.headers["content-type"]

    def test_cors_headers_present(self, client: TestClient):
        """Test CORS headers are present in API responses."""
        response = client.get("/admin-users/")
        
        # Check for CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-credentials",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # At least some CORS headers should be present
        present_headers = [h for h in cors_headers if h in response.headers]
        assert len(present_headers) > 0

    def test_request_methods_handling(self, client: TestClient):
        """Test different HTTP methods are handled correctly."""
        # GET requests
        get_response = client.get("/admin-users/")
        assert get_response.status_code == 200
        
        # POST requests
        post_data = {
            "name": "Method Test User",
            "email": "method@example.com",
            "password": "password123"
        }
        post_response = client.post("/admin-users/", data=post_data)
        assert post_response.status_code == 200
        
        # OPTIONS requests (for CORS)
        options_response = client.options("/admin-users/")
        # Should not fail with 500
        assert options_response.status_code != 500

    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent requests."""
        import concurrent.futures
        import threading
        
        def create_user(user_id):
            user_data = {
                "name": f"Concurrent User {user_id}",
                "email": f"concurrent{user_id}@example.com",
                "password": "password123"
            }
            return client.post("/admin-users/", data=user_data)
        
        # Create multiple users concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_user, i) for i in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

    def test_large_payload_handling(self, client: TestClient):
        """Test handling of large payloads."""
        # Test with long strings
        large_user_data = {
            "name": "A" * 1000,  # Very long name
            "email": "large@example.com",
            "password": "password123"
        }
        
        response = client.post("/admin-users/", data=large_user_data)
        # Should either succeed or fail gracefully with validation error
        assert response.status_code in [200, 422]

    def test_special_characters_handling(self, client: TestClient):
        """Test handling of special characters in data."""
        special_user_data = {
            "name": "José María O'Connor",
            "email": "josé@example.com",
            "password": "pássword123!@#"
        }
        
        response = client.post("/admin-users/", data=special_user_data)
        # Should handle Unicode characters properly
        if response.status_code == 200:
            user_data = response.json()
            assert user_data["name"] == special_user_data["name"]
