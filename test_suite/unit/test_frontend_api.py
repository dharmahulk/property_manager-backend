"""Unit tests for frontend API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
@pytest.mark.api
class TestFrontendAPI:
    """Test suite for frontend API endpoints."""

    def test_home_page_renders(self, client: TestClient):
        """Test that the home page renders successfully."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_home_page_contains_expected_content(self, client: TestClient):
        """Test that the home page contains expected HTML content."""
        response = client.get("/")
        
        content = response.text
        assert "<html" in content
        assert "<body" in content
        assert "<!DOCTYPE html>" in content

    def test_home_page_includes_auth_modals(self, client: TestClient):
        """Test that the home page includes authentication modals."""
        response = client.get("/")
        
        content = response.text
        assert "loginModal" in content
        assert "signupModal" in content

    def test_home_page_includes_css_and_js(self, client: TestClient):
        """Test that the home page includes required CSS and JS files."""
        response = client.get("/")
        
        content = response.text
        assert "modern.css" in content
        assert "modern-auth.js" in content

    def test_static_css_file_accessible(self, client: TestClient):
        """Test that the CSS file is accessible."""
        response = client.get("/static/css/modern.css")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/css")

    def test_static_js_file_accessible(self, client: TestClient):
        """Test that the JavaScript file is accessible."""
        response = client.get("/static/js/modern-auth.js")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/javascript")

    def test_static_file_not_found(self, client: TestClient):
        """Test handling of non-existent static files."""
        response = client.get("/static/nonexistent.css")
        
        assert response.status_code == 404

    def test_home_page_meta_tags(self, client: TestClient):
        """Test that the home page includes proper meta tags."""
        response = client.get("/")
        
        content = response.text
        assert '<meta charset="utf-8"' in content
        assert 'viewport' in content
        assert '<title>' in content

    def test_home_page_forms_structure(self, client: TestClient):
        """Test that the authentication forms have proper structure."""
        response = client.get("/")
        
        content = response.text
        # Login form
        assert 'id="loginForm"' in content
        assert 'name="email"' in content
        assert 'name="password"' in content
        
        # Signup form
        assert 'id="signupForm"' in content
        assert 'name="name"' in content
        assert 'name="confirm_password"' in content

    def test_home_page_bootstrap_integration(self, client: TestClient):
        """Test that Bootstrap CSS/JS is properly integrated."""
        response = client.get("/")
        
        content = response.text
        # Should include Bootstrap or similar CSS framework
        assert "bootstrap" in content.lower() or "css" in content

    def test_home_page_favicon(self, client: TestClient):
        """Test that favicon is properly referenced."""
        response = client.get("/")
        
        content = response.text
        assert "favicon" in content.lower()

    def test_home_page_responsive_design(self, client: TestClient):
        """Test that the page includes responsive design elements."""
        response = client.get("/")
        
        content = response.text
        assert "viewport" in content
        assert "width=device-width" in content
