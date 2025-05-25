from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings


# Create the engine that will interact with the database
DATABASE_URL = settings.DATABASE_URL  # Fetch from config settings
engine = create_engine(DATABASE_URL)

# Create a session maker that will be used to establish DB connections
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for our database models to inherit
Base = declarative_base()

# Dependency that provides a database session
def get_db():
    db = SessionLocal()  # Create a new session
    try:
        yield db  # Yield the session to the route
    finally:
        db.close()  # Ensure the session is closed after the
