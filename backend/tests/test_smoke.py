"""Health check + auth gate + profile-based login."""
from tests.conftest import PASSWORD


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_root(client):
    assert client.get("/").status_code == 200


def test_profiles_public(client):
    r = client.get("/profiles")
    assert r.status_code == 200
    assert any(p["name"] == "Chai" and p["avatar"] == "🐸" for p in r.json())


def test_protected_route_requires_login(client):
    assert client.get("/whoami").status_code == 401


def test_login_then_whoami_then_logout(client, admin_id):
    assert client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD}).status_code == 200
    me = client.get("/whoami").json()
    assert me["name"] == "Chai" and me["is_admin"] is True
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/whoami").status_code == 401


def test_wrong_password_rejected(client, admin_id):
    assert client.post("/auth/login", json={"user_id": admin_id, "password": "nope"}).status_code == 401
