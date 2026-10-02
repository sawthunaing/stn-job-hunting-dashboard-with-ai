import pytest

from app import ai, indeed, scraper

JK = "0123456789abcdef"


def test_parse_indeed_url_variants():
    for url in (
        f"https://uk.indeed.com/viewjob?jk={JK}",
        f"https://www.indeed.com/jobs?q=dev&vjk={JK}",
        f"https://indeed.co.uk/viewjob?jk={JK.upper()}&from=serp",
    ):
        key, canonical = indeed.parse_indeed_url(url)
        assert key == JK
        assert canonical.endswith(f"/viewjob?jk={JK}")


@pytest.mark.parametrize("url", [
    "https://evil.com/viewjob?jk=" + JK,
    "https://indeed.com.evil.com/viewjob?jk=" + JK,
    "https://uk.indeed.com/viewjob",
    "https://uk.indeed.com/viewjob?jk=short",
    "ftp://uk.indeed.com/viewjob?jk=" + JK,
])
def test_parse_indeed_url_rejects(url):
    with pytest.raises(indeed.NotIndeedURLError):
        indeed.parse_indeed_url(url)


def _extracted(**kw):
    return {"company": "Acme", "role": "Engineer", "location": "London",
            "description": "Build things", **kw}


def test_import_with_pasted_text_and_duplicate(client, monkeypatch):
    monkeypatch.setattr(ai, "extract_job_from_html", lambda text, url: _extracted())
    body = {"url": f"https://uk.indeed.com/viewjob?jk={JK}", "page_text": "Engineer at Acme ..."}
    r = client.post("/jobs/from-indeed", json=body)
    assert r.status_code == 201, r.text
    job = r.json()
    assert (job["company"], job["source"], job["platform"]) == ("Acme", "indeed", "Indeed")
    assert job["source_url"] == f"https://uk.indeed.com/viewjob?jk={JK}"

    dup = client.post("/jobs/from-indeed", json=body)
    assert dup.status_code == 409
    assert dup.json()["detail"]["job_id"] == job["id"]


def test_import_blocked_asks_for_pasted_text(client, monkeypatch):
    async def blocked(url):
        raise scraper.FetchBlockedError("HTTP 403")
    monkeypatch.setattr(scraper, "fetch_page", blocked)
    r = client.post("/jobs/from-indeed",
                    json={"url": "https://uk.indeed.com/viewjob?jk=fedcba9876543210"})
    assert r.status_code == 422
    assert "paste" in r.json()["detail"].lower()


def test_import_rejects_non_indeed(client):
    r = client.post("/jobs/from-indeed", json={"url": "https://example.com/?jk=" + JK})
    assert r.status_code == 400


def test_ai_failure_returns_502(client, monkeypatch):
    def boom(*a, **k):
        raise ai.AIError("AI returned a malformed response")
    monkeypatch.setattr(ai, "extract_job_from_html", boom)
    r = client.post("/jobs/from-indeed",
                    json={"url": "https://uk.indeed.com/viewjob?jk=aaaaaaaaaaaaaaaa", "page_text": "x"})
    assert r.status_code == 502


def test_tailor_rejects_unknown_doc_type(client):
    r = client.post("/jobs/1/tailor", json={"doc_type": "poem"})
    assert r.status_code == 422
