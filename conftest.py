import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app import app
from models.base import Base
from database import get_db
from config import TEST_DB_URL

TEST_DB_URL = TEST_DB_URL

#creating the test engine
test_engine = create_engine(
    TEST_DB_URL,
    pool_pre_ping = True, 
    pool_recycle = 3600
)

#creating the LocalSession for testing
TestingSessionLocal = sessionmaker(
    autocommit = False, 
    autoflush = False, 
    bind = test_engine
)

# ----Fixtures for database and client setup ----

@pytest.fixture(scope = "session", autouse = True)
def setup_test_db():
    print("Setting up the test database schema.")

    Base.metadata.create_all(bind = test_engine)

    yield

    print("Finished running all test cases.")

@pytest.fixture(scope = "function")
def test_session():
    connection = test_engine.connect()  
    transaction = connection.begin()

    db = TestingSessionLocal(bind = connection)

    yield db

    db.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope = "function")
def client(test_session):
    def override_get_db():
        try:
            yield test_session
        finally: 
            pass
        
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()