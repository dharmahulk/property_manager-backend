from sqlalchemy import Column, Integer, LargeBinary, String

from config import pg_sql_settings

class Image(pg_sql_settings.db_base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content_type = Column(String)
    data = Column(LargeBinary)