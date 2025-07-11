# backend/init_db.py

from models import Base
from database import engine

# Function to initialize the database (create tables)
def init():
    # Create all tables defined in the models
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully.")

if __name__ == "__main__":
    init()
