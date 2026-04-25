"""Unit tests for authentication schemas."""

import pytest
from pydantic import ValidationError

from auth.schemas import AdminUserCreate, AdminUserResponse


@pytest.mark.unit
@pytest.mark.auth
class TestAuthSchemas:
    """Test suite for authentication Pydantic schemas."""

    def test_admin_user_create_valid_data(self, valid_user_data):
        """Test AdminUserCreate with valid data."""
        user = AdminUserCreate(**valid_user_data)
        
        assert user.name == valid_user_data["name"]
        assert user.email == valid_user_data["email"]
        assert user.password == valid_user_data["password"]

    def test_admin_user_create_missing_name(self):
        """Test AdminUserCreate with missing name."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserCreate(
                email="test@example.com",
                password="password123"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_admin_user_create_missing_email(self):
        """Test AdminUserCreate with missing email."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserCreate(
                name="Test User",
                password="password123"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)

    def test_admin_user_create_missing_password(self):
        """Test AdminUserCreate with missing password."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserCreate(
                name="Test User",
                email="test@example.com"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)

    def test_admin_user_create_invalid_email(self):
        """Test AdminUserCreate with invalid email format."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserCreate(
                name="Test User",
                email="invalid-email",
                password="password123"
            )
        
        errors = exc_info.value.errors()
        # Check for email validation error
        assert any("email" in str(error).lower() for error in errors)

    def test_admin_user_create_empty_string_fields(self):
        """Test AdminUserCreate with empty string fields."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserCreate(
                name="",  # Empty name should fail with min_length=1
                email="test@example.com",
                password="password123"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_admin_user_create_short_password(self):
        """Test AdminUserCreate with password shorter than minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserCreate(
                name="Test User",
                email="test@example.com",
                password="123"  # Too short (< 6 characters)
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)

    def test_admin_user_response_valid_data(self):
        """Test AdminUserResponse with valid data."""
        user_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "is_active": True
        }
        
        user = AdminUserResponse(**user_data)
        
        assert user.id == 1
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_admin_user_response_missing_id(self):
        """Test AdminUserResponse with missing id."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserResponse(
                name="Test User",
                email="test@example.com",
                is_active=True
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("id",) for error in errors)

    def test_admin_user_response_missing_is_active(self):
        """Test AdminUserResponse with missing is_active field."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserResponse(
                id=1,
                name="Test User",
                email="test@example.com"
                # is_active field is required, no default
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("is_active",) for error in errors)

    def test_admin_user_response_invalid_email(self):
        """Test AdminUserResponse with invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserResponse(
                id=1,
                name="Test User",
                email="invalid-email",
                is_active=True
            )
        
        errors = exc_info.value.errors()
        assert any("email" in str(error).lower() for error in errors)

    def test_admin_user_response_json_serialization(self):
        """Test JSON serialization of AdminUserResponse."""
        user_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "is_active": True
        }
        
        user = AdminUserResponse(**user_data)
        json_data = user.model_dump()
        
        assert json_data == user_data

    def test_admin_user_response_from_orm(self, mock_admin_user):
        """Test creating AdminUserResponse from ORM model."""
        user = AdminUserResponse.model_validate(mock_admin_user)
        
        assert user.id == mock_admin_user.id
        assert user.name == mock_admin_user.name
        assert user.email == mock_admin_user.email
        assert user.is_active == mock_admin_user.is_active

    def test_admin_user_create_password_hashing(self, valid_user_data):
        """Test password hashing in AdminUserCreate."""
        user = AdminUserCreate(**valid_user_data)
        user_model = user.create_user_model
        
        # Verify that the password is hashed
        assert hasattr(user_model, 'hashed_password')
        assert user_model.hashed_password != valid_user_data["password"]
        assert len(user_model.hashed_password) > 20  # Hashed passwords are longer

    def test_admin_user_create_model_creation(self, valid_user_data):
        """Test model creation from AdminUserCreate."""
        user = AdminUserCreate(**valid_user_data)
        user_model = user.create_user_model
        
        assert user_model.name == valid_user_data["name"]
        assert user_model.email == valid_user_data["email"]
        assert hasattr(user_model, 'hashed_password')
        assert user_model.is_active is True  # Now explicitly set in create_user_model

    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user.name@domain.co.uk",
        "user+tag@example.org",
        "123@example.com"
    ])
    def test_valid_email_formats(self, email):
        """Test various valid email formats."""
        user = AdminUserCreate(
            name="Test User",
            email=email,
            password="password123"
        )
        assert user.email == email

    @pytest.mark.parametrize("invalid_email", [
        "invalid-email",
        "@example.com", 
        "user@",
        "user space@example.com",
        "",
        "user..user@example.com",  # Double dots
        "user@.com",  # Missing domain
        "user@domain.",  # Missing TLD
    ])
    def test_invalid_email_formats(self, invalid_email):
        """Test various invalid email formats."""
        with pytest.raises(ValidationError) as exc_info:
            AdminUserCreate(
                name="Test User",
                email=invalid_email,
                password="password123"
            )
        
        errors = exc_info.value.errors()
        # Should have email validation error
        assert any(error["loc"] == ("email",) for error in errors)
