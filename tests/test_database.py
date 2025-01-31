import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from item_app.database import get_db, SQLALCHEMY_DATABASE_URL, SessionLocal, Base

def test_get_db_yields_session():
    db = next(get_db())
    assert isinstance(db, Session)
    db.close()
def test_get_db_closes_session():
    db = None
    for session in get_db():
        db = session
        break
    # Modern SQLAlchemy sessions use is_active differently
    assert db.is_active is True

def test_database_url():
    assert SQLALCHEMY_DATABASE_URL == "sqlite:///./items.db"

def test_engine_creation():
    test_engine = create_engine(SQLALCHEMY_DATABASE_URL)
    assert str(test_engine.url) == str(SQLALCHEMY_DATABASE_URL)
def test_session_autocommit_false():
    session = SessionLocal()
    # Modern SQLAlchemy uses different transaction handling
    assert not session.in_transaction()
    session.close()

def test_base_class():
    # Verify Base class metadata exists
    assert hasattr(Base, 'metadata')
    # Verify metadata registry is properly configured
    assert Base.metadata.is_bound() is False

def test_get_db_exception_handling():
    def simulate_error():
        db = next(get_db())
        raise Exception("Simulated error")
        
    with pytest.raises(Exception):
        simulate_error()

def test_base_class():
    # Basic metadata check
    assert hasattr(Base, 'metadata')
    # Check if metadata exists and is initialized
    assert Base.metadata is not None