"""Shared fixtures: each test gets an isolated temp DB and a known password."""
import pytest
from fastapi.testclient import TestClient

from app import db as dbmod
from app.config import Settings, get_settings
from app.main import app

PASSWORD = "test-pass"


@pytest.fixture
def client(tmp_path):
    dbfile = tmp_path / "test.db"
    dbmod.init_db(dbfile)

    def _get_db():
        conn = dbmod.connect(dbfile)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    settings = Settings(app_password=PASSWORD, secret_key="test-secret", db_path=dbfile)
    app.dependency_overrides[dbmod.get_db] = _get_db
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    assert client.post("/auth/login", json={"password": PASSWORD}).status_code == 200
    return client
