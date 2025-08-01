# backend/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ✅ Load the DATABASE_URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# ✅ Function to create tables
def create_tables():
    from models import User, TestResult, TestRequest, Equipment  # Add all your models here
    Base.metadata.create_all(bind=engine)

# ✅ Dependency function for DB session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

