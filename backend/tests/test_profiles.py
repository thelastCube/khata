"""Multi-profile: hashing, admin gating, data isolation, password change."""
from tests.conftest import PASSWORD

from app.security import hash_password, verify_password


def test_password_hash_roundtrip():
    h = hash_password("secret")
    assert h != "secret" and "secret" not in h  # not stored readable
    assert verify_password("secret", h)
    assert not verify_password("nope", h)


def _make_friend(client, admin_id, name="Bob", pw="bobpass"):
    client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD})
    friend = client.post("/users", json={"name": name, "password": pw}).json()
    client.post("/auth/logout")
    return friend


def test_non_admin_cannot_manage_profiles(client, admin_id):
    friend = _make_friend(client, admin_id)
    client.post("/auth/login", json={"user_id": friend["id"], "password": "bobpass"})
    assert client.post("/users", json={"name": "X", "password": "y"}).status_code == 403
    assert client.get("/users").status_code == 403


def test_profiles_have_isolated_data(client, admin_id):
    friend = _make_friend(client, admin_id)

    client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD})
    client.post("/funds", json={"name": "AdminFund"})
    client.post("/auth/logout")

    client.post("/auth/login", json={"user_id": friend["id"], "password": "bobpass"})
    assert client.get("/funds").json() == []          # can't see admin's data
    client.post("/funds", json={"name": "BobFund"})
    assert [f["name"] for f in client.get("/funds").json()] == ["BobFund"]
    client.post("/auth/logout")

    client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD})
    assert [f["name"] for f in client.get("/funds").json()] == ["AdminFund"]


def test_change_password_then_relogin(client, admin_id):
    client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD})
    assert client.post("/me/password", json={"current_password": PASSWORD, "new_password": "newpass"}).status_code == 200
    client.post("/auth/logout")
    assert client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD}).status_code == 401
    assert client.post("/auth/login", json={"user_id": admin_id, "password": "newpass"}).status_code == 200


def test_cannot_delete_self_or_last_admin(client, admin_id):
    client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD})
    assert client.request("DELETE", f"/users/{admin_id}").status_code == 400  # last admin + self
