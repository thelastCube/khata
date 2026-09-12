"""Health check + auth gate."""
from tests.conftest import PASSWORD


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_root(client):
    assert client.get("/").status_code == 200


def test_protected_route_requires_login(client):
    assert client.get("/whoami").status_code == 401


def test_login_then_access_then_logout(client):
    assert client.post("/auth/login", json={"password": PASSWORD}).status_code == 200
    r = client.get("/whoami")
    assert r.status_code == 200 and r.json()["user"] == "owner"
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/whoami").status_code == 401


def test_wrong_password_rejected(client):
    assert client.post("/auth/login", json={"password": "nope"}).status_code == 401
