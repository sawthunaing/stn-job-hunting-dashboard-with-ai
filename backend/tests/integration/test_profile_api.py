"""Integration: profile read/upsert against the database."""
import pytest

pytestmark = pytest.mark.integration


def test_empty_profile_before_first_save(client, auth_headers):
    r = client.get("/profile", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["full_name"] is None and body["updated_at"] is None


def test_create_then_update_profile(client, auth_headers):
    r = client.put("/profile", json={"full_name": "Jane", "skills": "Python"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["full_name"] == "Jane"
    assert r.json()["updated_at"] is not None

    # PUT is a full replace: omitted fields are cleared
    r = client.put("/profile", json={"full_name": "Jane Doe"}, headers=auth_headers)
    assert r.json()["full_name"] == "Jane Doe"
    assert r.json()["skills"] is None

    assert client.get("/profile", headers=auth_headers).json()["full_name"] == "Jane Doe"


def test_client_supplied_updated_at_is_ignored(client, auth_headers):
    r = client.put("/profile", json={"full_name": "J", "updated_at": "2000-01-01T00:00:00"},
                   headers=auth_headers)
    assert not r.json()["updated_at"].startswith("2000")
