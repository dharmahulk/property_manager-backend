from sqlalchemy import Boolean, Column, Integer, String

from config import pg_sql_settings


class AdminUser(pg_sql_settings.db_base):
    __tablename__ = "AdminUser"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
