import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def session_factory():
    """Base de datos SQLite en memoria, nueva y vacía para cada test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # una sola conexión compartida (necesario en memoria)
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False)
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    """Cliente HTTP de pruebas que usa la base en memoria en lugar de PostgreSQL."""

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Sin "with": no se ejecuta el lifespan, que crearía tablas en tu Postgres real
    yield TestClient(app)
    app.dependency_overrides.clear()