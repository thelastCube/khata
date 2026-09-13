"""Shared fixtures. Everything (auth DB + per-profile data DBs) lives under a
temp data_dir, injected by overriding get_settings. We deliberately do NOT
enter the TestClient as a context manager, so the app lifespan (which would
touch the real data dir and migrate the real legacy DB) never runs in tests."""
import pytest
from fastapi.testclient import TestClient

from app.auth_db import init_auth_db
from app.config import Settings, get_settings
from app.main import app
from app.services.user_service import seed_default_admin

PASSWORD = "test-pass"  # this is what seed_default_admin uses for Chai (app_password)


@pytest.fixture
def settings(tmp_path):
    return Settings(app_password=PASSWORD, secret_key="test-secret",
                    data_dir=tmp_path, db_path=tmp_path / "legacy.db")


@pytest.fixture
def client(settings):
    init_auth_db(settings)
    seed_default_admin(settings)  # creates Chai (admin) with password == PASSWORD
    app.dependency_overrides[get_settings] = lambda: settings
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_id(client):
    profiles = client.get("/profiles").json()
    return next(p["id"] for p in profiles if p["name"] == "Chai")


@pytest.fixture
def auth_client(client, admin_id):
    assert client.post("/auth/login", json={"user_id": admin_id, "password": PASSWORD}).status_code == 200
    return client
