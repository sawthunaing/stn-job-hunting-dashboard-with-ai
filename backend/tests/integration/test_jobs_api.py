"""Integration: job CRUD, filtering and URL import."""
from datetime import datetime, timedelta

import pytest

from app import models
from app.db import SessionLocal

pytestmark = pytest.mark.integration


def create(client, headers, **fields):
    body = {"company": "Acme", "role": "Engineer", **fields}
    r = client.post("/jobs", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


class TestCrud:
    def test_create_applies_defaults(self, client, auth_headers):
        job = create(client, auth_headers, location="London")
        assert job["id"] > 0
        assert job["status"] == "New"
        assert job["currency"] == "GBP"
        assert job["starred"] is False
        assert job["analysis"] is None and job["suitability"] is None
        assert job["created_at"] and job["updated_at"]

    def test_create_requires_company_and_role(self, client, auth_headers):
        assert client.post("/jobs", json={"company": "Acme"}, headers=auth_headers).status_code == 422

    def test_get_and_404(self, client, auth_headers):
        job = create(client, auth_headers)
        assert client.get(f"/jobs/{job['id']}", headers=auth_headers).json()["company"] == "Acme"
        assert client.get("/jobs/9999", headers=auth_headers).status_code == 404

    def test_patch_only_changes_sent_fields(self, client, auth_headers):
        job = create(client, auth_headers, notes="keep me")
        r = client.patch(f"/jobs/{job['id']}",
                         json={"status": "Applied", "starred": True, "applied_date": "2026-09-01T10:00:00"},
                         headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "Applied" and body["starred"] is True
        assert body["applied_date"].startswith("2026-09-01")
        assert body["notes"] == "keep me"
        assert body["role"] == "Engineer"

    def test_patch_missing_job(self, client, auth_headers):
        assert client.patch("/jobs/9999", json={"status": "Applied"}, headers=auth_headers).status_code == 404

    def test_delete(self, client, auth_headers):
        job = create(client, auth_headers)
        r = client.delete(f"/jobs/{job['id']}", headers=auth_headers)
        assert r.status_code == 204 and r.content == b""
        assert client.get(f"/jobs/{job['id']}", headers=auth_headers).status_code == 404
        assert client.delete(f"/jobs/{job['id']}", headers=auth_headers).status_code == 404


class TestList:
    def test_list_item_shape(self, client, auth_headers):
        create(client, auth_headers, description="long text")
        [item] = client.get("/jobs", headers=auth_headers).json()
        assert set(item) == {"id", "company", "role", "location", "platform", "status",
                             "suitability", "starred", "created_at"}

    def test_newest_first(self, client, auth_headers):
        now = datetime.utcnow()
        with SessionLocal() as db:
            db.add_all([
                models.Job(company="Old", role="r", created_at=now - timedelta(days=2)),
                models.Job(company="New", role="r", created_at=now),
                models.Job(company="Mid", role="r", created_at=now - timedelta(days=1)),
            ])
            db.commit()
        companies = [j["company"] for j in client.get("/jobs", headers=auth_headers).json()]
        assert companies == ["New", "Mid", "Old"]

    def test_status_filter(self, client, auth_headers):
        create(client, auth_headers, company="A", status="Applied")
        create(client, auth_headers, company="B", status="New")
        applied = client.get("/jobs", params={"status_filter": "Applied"}, headers=auth_headers).json()
        assert [j["company"] for j in applied] == ["A"]
        everything = client.get("/jobs", params={"status_filter": "All"}, headers=auth_headers).json()
        assert len(everything) == 2

    def test_search_matches_company_or_role_case_insensitive(self, client, auth_headers):
        create(client, auth_headers, company="Monzo", role="Platform Engineer")
        create(client, auth_headers, company="Acme", role="Data Scientist")
        create(client, auth_headers, company="Beta", role="PLATFORM lead")

        def search(q):
            return sorted(j["company"] for j in
                          client.get("/jobs", params={"q": q}, headers=auth_headers).json())

        assert search("platform") == ["Beta", "Monzo"]
        assert search("monzo") == ["Monzo"]
        assert search("nothing") == []

    def test_filter_and_search_combined(self, client, auth_headers):
        create(client, auth_headers, company="Acme", status="Applied")
        create(client, auth_headers, company="Acme", status="Rejected")
        r = client.get("/jobs", params={"q": "acme", "status_filter": "Rejected"}, headers=auth_headers)
        assert [j["status"] for j in r.json()] == ["Rejected"]


class TestCreateFromUrl:
    def test_scrapes_extracts_and_saves(self, client, auth_headers, fake_claude, fake_fetch):
        url = "https://boards.greenhouse.io/acme/jobs/42"
        r = client.post("/jobs/from-url", json={"url": url}, headers=auth_headers)
        assert r.status_code == 201, r.text
        job = r.json()
        assert fake_fetch == [url]
        assert job["company"] == "Acme" and job["role"] == "Backend Engineer"
        assert job["platform"] == "Greenhouse"
        assert job["source_url"] == url
        assert job["work_type"] == "Hybrid"
        assert job["salary_min"] == 70 and job["salary_max"] == 90
        assert job["currency"] == "GBP"  # extractor returned null -> default
        assert job["status"] == "New"
        # the scraped page text is what was sent to Claude
        assert "Build APIs in Python." in fake_claude[0][1]
        # and it is persisted
        assert client.get(f"/jobs/{job['id']}", headers=auth_headers).json()["company"] == "Acme"

    def test_missing_fields_fall_back_to_unknown(self, client, auth_headers, fake_fetch, monkeypatch):
        from app import ai
        monkeypatch.setattr(ai, "extract_job_from_html", lambda html, url: {})
        job = client.post("/jobs/from-url", json={"url": "https://acme.com/careers/1"},
                          headers=auth_headers).json()
        assert job["company"] == "Unknown" and job["role"] == "Unknown"
        assert job["platform"] == "Direct"

    def test_fetch_failure_returns_400_and_saves_nothing(self, client, auth_headers, monkeypatch):
        from app import scraper

        async def boom(url):
            raise RuntimeError("403 Forbidden")

        monkeypatch.setattr(scraper, "fetch_page", boom)
        r = client.post("/jobs/from-url", json={"url": "https://linkedin.com/jobs/1"}, headers=auth_headers)
        assert r.status_code == 400
        assert "fetch failed" in r.json()["detail"]
        assert client.get("/jobs", headers=auth_headers).json() == []
