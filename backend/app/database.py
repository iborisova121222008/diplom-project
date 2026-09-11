from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine_options = {
    "pool_pre_ping": True
}

if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False
    }

if DATABASE_URL == "sqlite+pysqlite:///:memory:":
    engine_options["poolclass"] = StaticPool

engine = create_engine(
    DATABASE_URL,
    **engine_options
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


def get_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
