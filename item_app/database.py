"""
Database configuration and session management for SQLAlchemy.

This module sets up the SQLAlchemy database connection using SQLite,
creates the database engine, and provides session management utilities.

The database URL points to a local SQLite database file 'items.db'.
SessionLocal is configured for manual commit and flush operations.
The get_db function provides a database session context manager.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./items.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
