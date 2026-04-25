import pytest
from unittest.mock import patch, Mock, PropertyMock
import os

from config import ApiSettings, PostGresSQLSettings


@pytest.mark.unit
class TestApiSettings:
    """Test suite for API configuration settings."""

    def test_api_settings_default_values(self):
        """Test API settings with default values."""
        settings = ApiSettings()
        
        assert settings.PROJECT_NAME == "HI"
        assert settings.API_STR == ""
        assert settings.HOST_DOCS is True

    @patch.dict(os.environ, {
        'PROJECT_NAME': 'Test Project',
        'API_STR': '/api/v2',
        'HOST_DOCS': 'false'
    })
    def test_api_settings_from_environment(self):
        """Test API settings loaded from environment variables."""
        settings = ApiSettings()
        
        assert settings.PROJECT_NAME == "Test Project"
        assert settings.API_STR == "/api/v2"
        assert settings.HOST_DOCS is False

    @patch.dict(os.environ, {'HOST_DOCS': 'true'})
    def test_host_docs_true_from_env(self):
        """Test HOST_DOCS setting as true from environment."""
        settings = ApiSettings()
        assert settings.HOST_DOCS is True

    @patch.dict(os.environ, {'HOST_DOCS': 'True'})
    def test_host_docs_case_insensitive(self):
        """Test HOST_DOCS setting is case insensitive."""
        settings = ApiSettings()
        assert settings.HOST_DOCS is True


@pytest.mark.unit
class TestPostGresSQLSettings:
    """Test suite for PostgreSQL configuration settings."""

    @patch.dict(os.environ, {
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'testdb'
    })
    def test_postgresql_settings_from_environment(self):
        """Test PostgreSQL settings from environment variables."""
        settings = PostGresSQLSettings()
        
        assert settings.DB_USER == "testuser"
        assert settings.DB_PASSWORD == "testpass"
        assert settings.DB_HOST == "localhost"
        assert settings.DB_PORT == "5432"
        assert settings.DB_NAME == "testdb"

    @patch.dict(os.environ, {
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'testdb'
    })
    def test_database_url_generation(self):
        """Test database URL generation from settings."""
        settings = PostGresSQLSettings()
        
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert settings.pg_sql_database_url == expected_url

    def test_postgresql_settings_missing_env_vars(self):
        """Test PostgreSQL settings with missing environment variables."""
        # Settings should have default values
        settings = PostGresSQLSettings()
        
        assert hasattr(settings, 'DB_USER')
        assert hasattr(settings, 'pg_sql_database_url')

    @patch('config.create_engine')
    def test_database_engine_creation(self, mock_create_engine):
        """Test database engine creation."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        settings = PostGresSQLSettings()
        _ = settings.db_engine
        
        # Verify engine creation was called
        mock_create_engine.assert_called_once_with(settings.pg_sql_database_url)
        
    @patch('config.sessionmaker')
    def test_session_local_creation(self, mock_sessionmaker):
        """Test session local creation."""
        mock_session_class = Mock()
        mock_sessionmaker.return_value = mock_session_class
        
        # Mock the engine property first
        with patch.object(PostGresSQLSettings, 'db_engine', new_callable=PropertyMock) as mock_engine_prop:
            mock_engine = Mock()
            mock_engine_prop.return_value = mock_engine
            
            settings = PostGresSQLSettings()
            _ = settings.db_session
            
            # Verify sessionmaker was called
            mock_sessionmaker.assert_called_once_with(autocommit=False, autoflush=False, bind=mock_engine)

    @patch('config.PostGresSQLSettings.db_engine')
    def test_get_db_session_generator(self, mock_engine):
        """Test database session generator."""
        mock_session = Mock()
        mock_session_class = Mock(return_value=mock_session)
        
        settings = PostGresSQLSettings()
        settings.db_session = mock_session_class
        
        # Test session generator
        session_generator = settings.get_db_session()
        session = next(session_generator)
        
        assert session == mock_session
        
        # Verify session is closed
        try:
            next(session_generator)
        except StopIteration:
            mock_session.close.assert_called_once()

    def test_postgresql_settings_validation(self):
        """Test PostgreSQL settings validation."""
        settings = PostGresSQLSettings()
        
        # All required fields should be present
        assert hasattr(settings, 'DB_USER')
        assert hasattr(settings, 'DB_PASSWORD')
        assert hasattr(settings, 'DB_HOST')
        assert hasattr(settings, 'DB_PORT')
        assert hasattr(settings, 'DB_NAME')
        assert hasattr(settings, 'pg_sql_database_url')

    def test_database_url_format(self):
        """Test that database URL has correct format."""
        settings = PostGresSQLSettings()
        
        assert settings.pg_sql_database_url.startswith('postgresql://')
        assert '@' in settings.pg_sql_database_url
        assert ':' in settings.pg_sql_database_url
