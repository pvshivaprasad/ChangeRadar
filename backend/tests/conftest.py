import os
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.database import Base, get_db, init_db, SessionLocal
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    init_db()


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"
