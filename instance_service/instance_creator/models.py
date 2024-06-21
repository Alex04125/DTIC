# models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime

# Create a base class for model definitions
Base = declarative_base()

# Define the Instance model
class Instance(Base):
    __tablename__ = 'instance_registry'

    id = Column(Integer, primary_key=True, index=True)
    instance_name = Column(String(100), index=True, unique=True)
    module_name = Column(String(100), index=True)
    status = Column(String(50), default="Not done")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    container_status = Column(String(50), default="Not running")

class Module(Base):
    __tablename__ = 'module_registry'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, unique=True)  # Ensure uniqueness
    description = Column(String(500))
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status_updated_at = Column(DateTime, nullable=True)


