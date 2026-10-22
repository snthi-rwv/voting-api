import os

# Antes de importar la app: así los tests no dependen de tu .env ni de PostgreSQL
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "test-password"
os.environ["JWT_SECRET"] = "test-secret-key-with-at-least-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def admin_credentials():
    return {"username": "admin", "password": "test-password"}


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
def anon_client(session_factory):
    """Cliente SIN token, para probar que los endpoints protegidos rechazan el acceso."""

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


@pytest.fixture()
def client(anon_client, admin_credentials):
    """Cliente ya autenticado: hace login y envía el token en cada petición."""
    response = anon_client.post("/auth/login", data=admin_credentials)
    token = response.json()["access_token"]
    anon_client.headers.update({"Authorization": f"Bearer {token}"})
    return anon_client