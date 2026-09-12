import os

import pytest


os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-only-secret-that-is-long-enough-for-signing"
os.environ["JWT_ACCESS_TOKEN_MINUTES"] = "30"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from app.database import Base, SessionLocal, engine
from app.seed import import_canonical_artifacts


@pytest.fixture(scope="session", autouse=True)
def imported_database():
    Base.metadata.create_all(engine)

    with SessionLocal.begin() as session:
        import_canonical_artifacts(session)

    yield
