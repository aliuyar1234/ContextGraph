from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ocg.db.base import Base


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    LocalSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = LocalSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def now() -> datetime:
    return datetime(2026, 2, 7, 10, 0, 0, tzinfo=UTC)
