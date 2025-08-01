# backend/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ✅ Load the DATABASE_URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ PostgreSQL engine (no `connect_args` needed)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# ✅ Create session local
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ✅ Base class for models
Base = declarative_base()

# ✅ Function to create all tables
def create_tables():
    from models import User, TestResult, TestRequest, Equipment, Laboratory  # Add all your models
    Base.metadata.create_all(bind=engine)

# ✅ Dependency for injecting DB session
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
