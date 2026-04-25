from functools import cached_property

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
    DB_USER: str = "postgres.dbtsryjnsufsmobqoixs"
    DB_PASSWORD: str = "Dharmadon36@hulk"
    DB_HOST: str = "aws-0-ap-south-1.pooler.supabase.com"
    DB_PORT: str = "5432"
    DB_NAME: str = "postgres"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

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

api_settings = ApiSettings()
pg_sql_settings = PostGresSQLSettings()