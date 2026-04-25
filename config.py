from functools import cached_property

import os
from typing import Optional
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class ApiSettings(BaseSettings):
    PROJECT_NAME: str = "HI"
    API_STR: str = ""
    API_PREFIX: str = "/money_tracker"

    HOST_DOCS: bool = True
    DEBUG: bool = False

    SERVICE_HOST: str = "localhost"
    SERVICE_PORT: int = 8000

    CORS_ORIGINS_REGEX: Optional[str] = None

    LOGGING_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "loggers": {
            "creative_manager": {
                "handlers": ["console"],
                "level": "INFO"
            }
        }
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
class PostGresSQLSettings(BaseSettings):
    # Read from environment variables with fallbacks
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "postgres")

    @cached_property
    def pg_sql_database_url(self):
        return f"postgresql://{self.DB_USER}:%s@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"% quote_plus(self.DB_PASSWORD)
    
    @cached_property
    def db_engine(self):
        return create_engine(self.pg_sql_database_url)
    
    @cached_property
    def db_session(self):
        return sessionmaker(autocommit=False, autoflush=False, bind=self.db_engine)
    
    @cached_property
    def db_base(self):
        return declarative_base()
    
    def get_db_session(self):
        db = self.db_session()
        try:
            yield db
        finally:
            db.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            print(f"Testing connection to: {self.DB_HOST}:{self.DB_PORT}")
            print(f"Database: {self.DB_NAME}")
            print(f"User: {self.DB_USER}")
            
            engine = self.db_engine
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
                print("✅ Database connection successful!")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print(f"Connection URL (without password): postgresql://{self.DB_USER}:***@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
            return False

api_settings = ApiSettings()
pg_sql_settings = PostGresSQLSettings()