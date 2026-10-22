import pytest

from app.security import create_access_token


def test_login_returns_token(anon_client, admin_credentials):
    response = anon_client.post("/auth/login", data=admin_credentials)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_wrong_password_returns_401(anon_client):
    response = anon_client.post("/auth/login", data={"username": "admin", "password": "mala"})
    assert response.status_code == 401


def test_login_with_wrong_username_returns_401(anon_client):
    response = anon_client.post("/auth/login", data={"username": "otro", "password": "test-password"})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/voters"),
        ("post", "/voters"),
        ("delete", "/voters/1"),
        ("get", "/candidates"),
        ("post", "/candidates"),
        ("get", "/votes"),
        ("post", "/votes"),
    ],
)
def test_protected_endpoints_require_token(anon_client, method, path):
    response = getattr(anon_client, method)(path)
    assert response.status_code == 401


def test_invalid_token_returns_401(anon_client):
    response = anon_client.get("/candidates", headers={"Authorization": "Bearer token-falso"})
    assert response.status_code == 401


def test_expired_token_returns_401(anon_client):
    expired = create_access_token("admin", expires_minutes=-1)
    response = anon_client.get("/candidates", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_token_for_other_user_returns_401(anon_client):
    token = create_access_token("intruso")
    response = anon_client.get("/candidates", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_public_endpoints_need_no_token(anon_client):
    assert anon_client.get("/").status_code == 200
    assert anon_client.get("/votes/statistics").status_code == 200