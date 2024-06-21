from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Module(Base):
    __tablename__ = 'module_registry'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, unique=True)  # Ensure uniqueness
    description = Column(String(500))
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status_updated_at = Column(DateTime, nullable=True)
