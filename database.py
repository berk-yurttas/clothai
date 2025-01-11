from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Get database path from environment variable or use default
DB_PATH = os.getenv('SQLITE_DB_PATH', './clothai.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Create database engine
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

class DeviceTryCount(Base):
    __tablename__ = "device_try_counts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    try_count_left = Column(Integer, default=3)
    last_updated = Column(DateTime, default=datetime.utcnow)

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
