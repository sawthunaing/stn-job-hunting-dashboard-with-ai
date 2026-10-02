"""Integration: AI endpoints persist Claude's output on the job record."""
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def job(client, auth_headers):
    r = client.post("/jobs", json={"company": "Acme", "role": "Engineer", "location": "London",
                                   "description": "Build APIs in Python."}, headers=auth_headers)
    return r.json()


@pytest.fixture
def job_without_description(client, auth_headers):
    return client.post("/jobs", json={"company": "Acme", "role": "Engineer"}, headers=auth_headers).json()


@pytest.fixture
def saved_profile(client, auth_headers):
    client.put("/profile", json={"full_name": "Jane Doe", "skills": "Python",
                                 "private_notes": "SECRET-NOTE", "target_salary": "£999k"},
               headers=auth_headers)


class TestAnalyze:
    def test_stores_analysis_and_score(self, client, auth_headers, job, saved_profile, fake_claude):
        r = client.post(f"/jobs/{job['id']}/analyze", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["suitability"] == 82
        assert body["analysis"]["gaps"][0]["skill"] == "Kubernetes"
        assert body["analyzed_at"] is not None
        # persisted + surfaced in list view
        [item] = client.get("/jobs", headers=auth_headers).json()
        assert item["suitability"] == 82
        # the stored profile (including private targeting) is sent for analysis
        system, user = fake_claude[0]
        assert "Jane Doe" in user and "SECRET-NOTE" in user and "London" in user

    def test_requires_description(self, client, auth_headers, job_without_description, fake_claude):
        r = client.post(f"/jobs/{job_without_description['id']}/analyze", headers=auth_headers)
        assert r.status_code == 400
        assert fake_claude == []

    def test_missing_job(self, client, auth_headers, fake_claude):
        assert client.post("/jobs/9999/analyze", headers=auth_headers).status_code == 404


class TestPrep:
    def test_stores_prep(self, client, auth_headers, job, fake_claude):
        body = client.post(f"/jobs/{job['id']}/prep", headers=auth_headers).json()
        assert body["interview_prep"]["technical"][0]["q"] == "Design a queue"

    def test_requires_description(self, client, auth_headers, job_without_description, fake_claude):
        assert client.post(f"/jobs/{job_without_description['id']}/prep",
                           headers=auth_headers).status_code == 400

    def test_missing_job(self, client, auth_headers, fake_claude):
        assert client.post("/jobs/9999/prep", headers=auth_headers).status_code == 404


class TestResearch:
    def test_works_without_description(self, client, auth_headers, job_without_description, fake_claude):
        r = client.post(f"/jobs/{job_without_description['id']}/research", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["company_research"]["talking_points"] == ["Scale"]

    def test_missing_job(self, client, auth_headers, fake_claude):
        assert client.post("/jobs/9999/research", headers=auth_headers).status_code == 404


class TestTailor:
    def test_multiple_doc_types_accumulate(self, client, auth_headers, job, saved_profile, fake_claude):
        url = f"/jobs/{job['id']}/tailor"
        r1 = client.post(url, json={"doc_type": "cv"}, headers=auth_headers)
        r2 = client.post(url, json={"doc_type": "cover_letter"}, headers=auth_headers)
        assert r1.status_code == r2.status_code == 200
        docs = client.get(f"/jobs/{job['id']}", headers=auth_headers).json()["tailored_docs"]
        assert set(docs) == {"cv", "cover_letter"}
        assert docs["cv"]["ats_match_pct"] == 77

    def test_private_profile_fields_never_sent(self, client, auth_headers, job, saved_profile, fake_claude):
        client.post(f"/jobs/{job['id']}/tailor", json={"doc_type": "cv"}, headers=auth_headers)
        _, user = fake_claude[0]
        assert "Jane Doe" in user
        assert "SECRET-NOTE" not in user and "£999k" not in user

    def test_regenerating_overwrites_same_doc_type(self, client, auth_headers, job, fake_claude, monkeypatch):
        from app import ai
        url = f"/jobs/{job['id']}/tailor"
        client.post(url, json={"doc_type": "cv"}, headers=auth_headers)
        monkeypatch.setattr(ai, "tailor_doc", lambda *a: {"content": "v2"})
        docs = client.post(url, json={"doc_type": "cv"}, headers=auth_headers).json()["tailored_docs"]
        assert docs == {"cv": {"content": "v2"}}

    def test_requires_description(self, client, auth_headers, job_without_description, fake_claude):
        r = client.post(f"/jobs/{job_without_description['id']}/tailor", json={"doc_type": "cv"},
                        headers=auth_headers)
        assert r.status_code == 400

    def test_body_validation(self, client, auth_headers, job, fake_claude):
        assert client.post(f"/jobs/{job['id']}/tailor", json={}, headers=auth_headers).status_code == 422


def test_full_application_workflow(client, auth_headers, saved_profile, fake_claude, fake_fetch):
    """Import from URL -> analyze -> prep -> research -> tailor CV -> mark applied."""
    job = client.post("/jobs/from-url", json={"url": "https://jobs.lever.co/acme/1"},
                      headers=auth_headers).json()
    jid = job["id"]
    for step in ("analyze", "prep", "research"):
        assert client.post(f"/jobs/{jid}/{step}", headers=auth_headers).status_code == 200
    assert client.post(f"/jobs/{jid}/tailor", json={"doc_type": "cv"}, headers=auth_headers).status_code == 200
    client.patch(f"/jobs/{jid}", json={"status": "Applied"}, headers=auth_headers)

    final = client.get(f"/jobs/{jid}", headers=auth_headers).json()
    assert final["platform"] == "Lever"
    assert final["status"] == "Applied"
    assert final["suitability"] == 82
    assert all(final[k] for k in ("analysis", "interview_prep", "company_research", "tailored_docs"))
    assert len(fake_claude) == 5  # extract + analyze + prep + research + tailor
