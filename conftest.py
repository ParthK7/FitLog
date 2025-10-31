import pytest
from fastapi.testclient import TestClient

from app import app
from models.base import Base
from database import get_db

# We'll use a synchronous in-memory SQLite engine for tests and provide a small
# async shim that exposes the AsyncSession-like methods the async endpoints expect.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import asyncio


class AsyncSessionShim:
    """A tiny shim that wraps a sync SQLAlchemy Session and exposes async methods
    used by the application (scalars, commit, refresh, rollback, add, delete).

    Under the hood the sync operations run in a threadpool so the async
    endpoints can await them while the real work is performed synchronously.
    """

    def __init__(self, sync_session):
        self._session = sync_session

    async def scalars(self, statement):
        # Run the sync SQLAlchemy call directly on the same thread where the
        # TestClient runs the app. Running in-thread avoids cross-thread use of
        # the same Session object.
        result = self._session.execute(statement)
        rows = list(result.scalars())

        class _Res:
            def __init__(self, items):
                self._items = items

            def first(self):
                return self._items[0] if self._items else None

            def one_or_none(self):
                if len(self._items) == 1:
                    return self._items[0]
                if len(self._items) == 0:
                    return None
                raise Exception("Multiple rows returned when one_or_none expected")

            def all(self):
                return self._items

        return _Res(rows)

    async def execute(self, statement):
        return self._session.execute(statement)

    async def commit(self):
        self._session.commit()

    async def rollback(self):
        self._session.rollback()

    async def refresh(self, instance):
        self._session.refresh(instance)

    def add(self, instance):
        # SQLAlchemy AsyncSession.add is synchronous; the app calls db.add(...)
        # without awaiting, so provide a synchronous add here.
        self._session.add(instance)

    async def delete(self, instance):
        self._session.delete(instance)

    # Provide context manager support if code uses `async with get_db()`
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


from sqlalchemy.pool import StaticPool

# Session-scoped synchronous engine and sessionmaker for tests
# Use StaticPool + check_same_thread=False so the in-memory SQLite database is
# shared across threads/connections used by TestClient.
ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SyncSessionLocal = sessionmaker(bind=ENGINE)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create the test schema once per session and tear it down afterwards."""
    # Ensure model classes are imported so their tables are registered on Base.metadata
    # before create_all() runs.
    import models.user
    import models.exercise
    import models.workout
    import models.workout_exercise

    Base.metadata.create_all(bind=ENGINE)
    yield
    Base.metadata.drop_all(bind=ENGINE)


@pytest.fixture(scope="function")
def client():
    """Provide a TestClient and override `get_db` with an async shim backed by a
    synchronous SQLite session.
    """

    # Ensure each test starts with a fresh schema so tests are isolated.
    Base.metadata.drop_all(bind=ENGINE)
    Base.metadata.create_all(bind=ENGINE)

    async def override_get_db():
        # create a fresh sync session for each request and yield the async shim
        sync_sess = SyncSessionLocal()
        try:
            yield AsyncSessionShim(sync_sess)
        finally:
            sync_sess.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()
