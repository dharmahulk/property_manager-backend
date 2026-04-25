"""Unit tests for authentication services."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from auth.services import AdminUserService
from auth.models import AdminUser
from auth.schemas import AdminUserCreate


@pytest.mark.unit
@pytest.mark.auth
class TestAdminUserService:
    """Test suite for AdminUserService."""

    def test_create_user_success(self, mock_db_session, valid_user_data):
        """Test successful user creation."""
        # Create user schema
        user_create = AdminUserCreate(**valid_user_data)
        user_model = user_create.create_user_model
        
        # Mock database operations
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Call service method
        result = AdminUserService.create(mock_db_session, user_model)
        
        # Verify database operations were called
        mock_db_session.add.assert_called_once_with(user_model)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(user_model)
        
        # Verify return value
        assert result == user_model

    def test_get_user_by_email_found(self, mock_db_session, mock_admin_user):
        """Test getting user by email when user exists."""
        email = "test@example.com"
        
        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock(return_value=mock_admin_user)
        
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_admin_user
        
        # Call service method
        result = AdminUserService.get_user_by_email(mock_db_session, email)
        
        # Verify query was called correctly
        mock_db_session.query.assert_called_once_with(AdminUser)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
        
        # Verify return value
        assert result == mock_admin_user

    def test_get_user_by_email_not_found(self, mock_db_session):
        """Test getting user by email when user doesn't exist."""
        email = "nonexistent@example.com"
        
        # Mock query chain returning None
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        # Call service method
        result = AdminUserService.get_user_by_email(mock_db_session, email)
        
        # Verify return value is None
        assert result is None

    def test_get_by_id_found(self, mock_db_session, mock_admin_user):
        """Test getting user by ID when user exists."""
        user_id = 1
        
        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_admin_user
        
        # Call service method
        result = AdminUserService.get_by_id(mock_db_session, user_id)
        
        # Verify query was called correctly
        mock_db_session.query.assert_called_once_with(AdminUser)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()
        
        # Verify return value
        assert result == mock_admin_user

    def test_get_by_id_not_found(self, mock_db_session):
        """Test getting user by ID when user doesn't exist."""
        user_id = 999
        
        # Mock query chain returning None
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        # Call service method
        result = AdminUserService.get_by_id(mock_db_session, user_id)
        
        # Verify return value is None
        assert result is None

    def test_get_all_with_pagination(self, mock_db_session):
        """Test getting all users with pagination."""
        skip = 0
        limit = 10
        mock_users = [Mock() for _ in range(5)]
        
        # Mock query chain
        mock_query = Mock()
        mock_offset = Mock()
        mock_limit_query = Mock()
        
        mock_db_session.query.return_value = mock_query
        mock_query.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit_query
        mock_limit_query.all.return_value = mock_users
        
        # Call service method
        result = AdminUserService.get_all(mock_db_session, skip=skip, limit=limit)
        
        # Verify query was called correctly
        mock_db_session.query.assert_called_once_with(AdminUser)
        mock_query.offset.assert_called_once_with(skip)
        mock_offset.limit.assert_called_once_with(limit)
        mock_limit_query.all.assert_called_once()
        
        # Verify return value
        assert result == mock_users

    def test_get_all_default_pagination(self, mock_db_session):
        """Test getting all users with default pagination."""
        mock_users = [Mock() for _ in range(3)]
        
        # Mock query chain
        mock_query = Mock()
        mock_offset = Mock()
        mock_limit_query = Mock()
        
        mock_db_session.query.return_value = mock_query
        mock_query.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit_query
        mock_limit_query.all.return_value = mock_users
        
        # Call service method with default parameters
        result = AdminUserService.get_all(mock_db_session)
        
        # Verify default pagination was used
        mock_query.offset.assert_called_once_with(0)
        mock_offset.limit.assert_called_once_with(100)
        
        # Verify return value
        assert result == mock_users

    def test_create_user_database_error(self, mock_db_session, valid_user_data):
        """Test user creation when database error occurs."""
        # Create user schema
        user_create = AdminUserCreate(**valid_user_data)
        user_model = user_create.create_user_model
        
        # Mock database error
        mock_db_session.commit.side_effect = Exception("Database error")
        
        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            AdminUserService.create(mock_db_session, user_model)
        
        assert "Database error" in str(exc_info.value)
        
        # Verify add was called but commit failed
        mock_db_session.add.assert_called_once_with(user_model)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.parametrize("skip,limit", [
        (0, 10),
        (10, 20),
        (50, 5),
        (0, 100)
    ])
    def test_get_all_various_pagination(self, mock_db_session, skip, limit):
        """Test get_all with various pagination parameters."""
        mock_users = [Mock() for _ in range(limit)]
        
        # Mock query chain
        mock_query = Mock()
        mock_offset = Mock()
        mock_limit_query = Mock()
        
        mock_db_session.query.return_value = mock_query
        mock_query.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit_query
        mock_limit_query.all.return_value = mock_users
        
        # Call service method
        result = AdminUserService.get_all(mock_db_session, skip=skip, limit=limit)
        
        # Verify pagination parameters
        mock_query.offset.assert_called_once_with(skip)
        mock_offset.limit.assert_called_once_with(limit)
        
        # Verify return value
        assert result == mock_users
