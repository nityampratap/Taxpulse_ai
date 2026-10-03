import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def db():
    from app.db.session import SessionLocal, engine, Base
    Base.metadata.create_all(engine)
    session = SessionLocal()
    # Ensure test isolation by clearing tables
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
