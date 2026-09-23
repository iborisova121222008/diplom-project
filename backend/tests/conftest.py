import os

import pytest


os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["JWT_SECRET"] = "test-secret-key-for-local-test-runs-only"
os.environ["JWT_ACCESS_TOKEN_MINUTES"] = "60"

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.seed import import_canonical_artifacts


RESEARCHER_ID = "test.researcher"
RESEARCHER_PASSWORD = "TestPass1!"


@pytest.fixture(scope="session", autouse=True)
def imported_database():
    Base.metadata.create_all(engine)

    with SessionLocal.begin() as session:
        import_canonical_artifacts(session)

    yield


@pytest.fixture(scope="session")
def anonymous_client():
    return TestClient(app)


@pytest.fixture(scope="session")
def client(anonymous_client):
    """Test client carrying the bearer token the scientific API requires."""
    response = anonymous_client.post(
        "/api/auth/register",
        json={
            "researcher_id": RESEARCHER_ID,
            "password": RESEARCHER_PASSWORD,
        },
    )

    assert response.status_code == 201, response.text
    authenticated = TestClient(app)
    authenticated.headers["Authorization"] = (
        f"Bearer {response.json()['access_token']}"
    )
    return authenticated
