"""Integration: login flow and route protection."""
import pytest

from app import auth
from app.config import settings

pytestmark = pytest.mark.integration


def test_health_is_public(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_demo_info_is_public(client):
    assert client.get("/demo-info").json() == {"demo_mode": False}


def test_login_success_returns_usable_token(client):
    r = client.post("/auth/login", json={"username": "tester", "password": "s3cret-test-password"})
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "tester"
    assert body["expires_in_hours"] == settings.jwt_ttl_hours
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200 and me.json() == {"username": "tester"}


@pytest.mark.parametrize("creds", [
    {"username": "tester", "password": "wrong"},
    {"username": "nobody", "password": "s3cret-test-password"},
])
def test_login_bad_credentials(client, creds):
    r = client.post("/auth/login", json=creds)
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid credentials"


def test_login_validation_error(client):
    assert client.post("/auth/login", json={"username": "tester"}).status_code == 422


@pytest.mark.parametrize("method,path", [
    ("get", "/auth/me"),
    ("get", "/profile"),
    ("put", "/profile"),
    ("get", "/jobs"),
    ("get", "/jobs/1"),
    ("post", "/jobs"),
    ("patch", "/jobs/1"),
    ("delete", "/jobs/1"),
    ("post", "/jobs/1/analyze"),
    ("post", "/jobs/1/tailor"),
])
def test_protected_routes_require_token(client, method, path):
    r = getattr(client, method)(path)
    assert r.status_code == 401


def test_invalid_and_expired_tokens_rejected(client, monkeypatch):
    assert client.get("/jobs", headers={"Authorization": "Bearer garbage"}).status_code == 401
    monkeypatch.setattr(settings, "jwt_ttl_hours", -1)
    expired = auth.issue_token("tester")
    monkeypatch.setattr(settings, "jwt_ttl_hours", 1)
    assert client.get("/jobs", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


class TestDemoMode:
    def test_reads_are_public(self, client, demo_mode):
        assert client.get("/demo-info").json() == {"demo_mode": True}
        assert client.get("/jobs").status_code == 200
        assert client.get("/profile").status_code == 200
        assert client.get("/auth/me").json() == {"username": "demo-visitor"}

    def test_writes_forbidden_even_with_valid_token(self, client, auth_headers, demo_mode):
        r = client.post("/jobs", json={"company": "A", "role": "B"}, headers=auth_headers)
        assert r.status_code == 403
        assert "read-only" in r.json()["detail"]
        assert client.put("/profile", json={}, headers=auth_headers).status_code == 403
        assert client.post("/jobs/1/analyze", headers=auth_headers).status_code == 403
