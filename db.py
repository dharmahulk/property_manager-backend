"""
Database utilities and session management.
"""
from typing import Generator
from sqlalchemy.orm import Session

from config import pg_sql_settings


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = pg_sql_settings.db_session()
    try:
        yield db
    finally:
        db.close()


def test_db_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        print(f"Testing connection to: {pg_sql_settings.DB_HOST}:{pg_sql_settings.DB_PORT}")
        print(f"Database: {pg_sql_settings.DB_NAME}")
        print(f"User: {pg_sql_settings.DB_USER}")
        
        engine = pg_sql_settings.db_engine
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print(f"Connection URL (without password): postgresql://{pg_sql_settings.DB_USER}:***@{pg_sql_settings.DB_HOST}:{pg_sql_settings.DB_PORT}/{pg_sql_settings.DB_NAME}")
        return False