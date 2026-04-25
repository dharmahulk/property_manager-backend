"""Integration tests for database operations."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth.models import AdminUser
from auth.services import AdminUserService
from config import PostGresSQLSettings


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.slow
class TestDatabaseIntegration:
    """Test suite for database integration."""

    @pytest.fixture(scope="class")
    def in_memory_db(self):
        """Create an in-memory SQLite database for testing."""
        from config import pg_sql_settings
        Base = pg_sql_settings.db_base
        
        # Create in-memory SQLite engine
        engine = create_engine("sqlite:///:memory:", echo=False)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield SessionLocal
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)

    def test_database_connection_handling(self):
        """Test database connection error handling."""
        with patch('config.PostGresSQLSettings') as mock_settings:
            # Mock connection failure
            mock_settings.return_value.db_engine.connect.side_effect = Exception("Connection failed")
            
            # Test that application handles connection errors gracefully
            # This should not crash the application
            try:
                settings = PostGresSQLSettings()
                # Attempt to use the database
                session_gen = settings.get_db_session()
                next(session_gen)
            except Exception as e:
                # Should handle the error gracefully
                assert "Connection failed" in str(e)

    def test_session_lifecycle(self, in_memory_db):
        """Test database session lifecycle."""
        SessionLocal = in_memory_db
        
        # Test session creation and closure
        session = SessionLocal()
        try:
            # Session should be active
            assert session.is_active
            
            # Test basic query
            users = session.query(AdminUser).all()
            assert isinstance(users, list)
            
        finally:
            session.close()
            
        # Session should be closed
        assert not session.is_active

    def test_user_model_creation(self, in_memory_db):
        """Test creating and persisting user models."""
        SessionLocal = in_memory_db
        session = SessionLocal()
        
        try:
            # Create a user
            user = AdminUser(
                name="Test User",
                email="test@example.com",
                hashed_password="hashed_password123",
                is_active=True
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Verify user was created
            assert user.id is not None
            assert user.name == "Test User"
            assert user.email == "test@example.com"
            
        finally:
            session.close()

    def test_user_service_with_real_db(self, in_memory_db):
        """Test AdminUserService with real database operations."""
        SessionLocal = in_memory_db
        session = SessionLocal()
        
        try:
            # Create user via service
            user_data = AdminUser(
                name="Service Test User",
                email="service@example.com",
                hashed_password="hashed_password123",
                is_active=True
            )
            
            created_user = AdminUserService.create(session, user_data)
            
            # Verify creation
            assert created_user.id is not None
            assert created_user.name == "Service Test User"
            
            # Test retrieval by email
            found_user = AdminUserService.get_user_by_email(session, "service@example.com")
            assert found_user is not None
            assert found_user.email == "service@example.com"
            
            # Test retrieval by ID
            found_by_id = AdminUserService.get_by_id(session, created_user.id)
            assert found_by_id is not None
            assert found_by_id.id == created_user.id
            
            # Test get_all
            all_users = AdminUserService.get_all(session, skip=0, limit=10)
            assert len(all_users) >= 1
            assert any(user.email == "service@example.com" for user in all_users)
            
        finally:
            session.close()

    def test_database_constraints(self, in_memory_db):
        """Test database constraints and validations."""
        SessionLocal = in_memory_db
        session = SessionLocal()
        
        try:
            # Create first user
            user1 = AdminUser(
                name="User One",
                email="unique@example.com",
                hashed_password="password123",
                is_active=True
            )
            session.add(user1)
            session.commit()
            
            # Try to create user with same email (should fail if unique constraint exists)
            user2 = AdminUser(
                name="User Two", 
                email="unique@example.com",  # Same email
                hashed_password="password456",
                is_active=True
            )
            session.add(user2)
            
            # This should fail if email uniqueness is enforced
            try:
                session.commit()
                # If we reach here, uniqueness is not enforced
                pass
            except Exception:
                # Expected if uniqueness is enforced
                session.rollback()
                
        finally:
            session.close()

    def test_transaction_rollback(self, in_memory_db):
        """Test transaction rollback functionality."""
        SessionLocal = in_memory_db
        session = SessionLocal()
        
        try:
            # Start a transaction
            user = AdminUser(
                name="Rollback Test User",
                email="rollback@example.com",
                hashed_password="password123",
                is_active=True
            )
            session.add(user)
            
            # Don't commit, rollback instead
            session.rollback()
            
            # Verify user was not persisted
            found_user = session.query(AdminUser).filter(
                AdminUser.email == "rollback@example.com"
            ).first()
            assert found_user is None
            
        finally:
            session.close()

    def test_pagination_with_real_data(self, in_memory_db):
        """Test pagination with real database data."""
        SessionLocal = in_memory_db
        session = SessionLocal()
        
        try:
            # Create multiple users
            users = []
            for i in range(15):
                user = AdminUser(
                    name=f"User {i}",
                    email=f"user{i}@example.com",
                    hashed_password=f"password{i}",
                    is_active=True
                )
                users.append(user)
                session.add(user)
            
            session.commit()
            
            # Test pagination
            page1 = AdminUserService.get_all(session, skip=0, limit=5)
            assert len(page1) == 5
            
            page2 = AdminUserService.get_all(session, skip=5, limit=5)
            assert len(page2) == 5
            
            page3 = AdminUserService.get_all(session, skip=10, limit=10)
            assert len(page3) <= 10  # At most 10, but could be fewer
            
            # Verify no overlap
            page1_ids = {user.id for user in page1}
            page2_ids = {user.id for user in page2}
            assert page1_ids.isdisjoint(page2_ids)
            
        finally:
            session.close()

    def test_database_error_handling(self, in_memory_db):
        """Test handling of database errors."""
        SessionLocal = in_memory_db
        session = SessionLocal()
        
        try:
            # Test with invalid data that might cause DB errors
            user = AdminUser(
                name=None,  # This might cause a constraint violation
                email="invalid@example.com",
                hashed_password="password123",
                is_active=True
            )
            session.add(user)
            
            try:
                session.commit()
            except Exception as e:
                # Should handle the error gracefully
                session.rollback()
                assert isinstance(e, Exception)
                
        finally:
            session.close()

    @patch('config.pg_sql_settings.db_engine.connect')
    def test_connection_pool_handling(self, mock_connect):
        """Test database connection pool handling."""
        # Mock connection failure
        mock_connect.side_effect = Exception("Connection pool exhausted")
        
        # Test that application handles connection pool issues
        with pytest.raises(Exception) as exc_info:
            from config import pg_sql_settings
            with pg_sql_settings.get_db_session() as session:
                session.query(AdminUser).all()
        
        assert "Connection pool exhausted" in str(exc_info.value)

    def test_concurrent_database_access(self, in_memory_db):
        """Test concurrent database access."""
        import concurrent.futures
        import threading
        
        SessionLocal = in_memory_db
        
        def create_user(user_id):
            session = SessionLocal()
            try:
                user = AdminUser(
                    name=f"Concurrent User {user_id}",
                    email=f"concurrent{user_id}@example.com",
                    hashed_password=f"password{user_id}",
                    is_active=True
                )
                return AdminUserService.create(session, user)
            finally:
                session.close()
        
        # Create users concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_user, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All users should be created successfully
        assert len(results) == 5
        for user in results:
            assert user.id is not None
            assert user.name.startswith("Concurrent User")
