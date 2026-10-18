import pytest

from app import ai, cvlibrary, scraper
from app.config import settings

JOB_ID = "223456789"
CANONICAL = f"https://www.cv-library.co.uk/job/{JOB_ID}"


@pytest.mark.parametrize("url", [
    f"https://www.cv-library.co.uk/job/{JOB_ID}/Software-Developer",
    f"https://www.cv-library.co.uk/job/{JOB_ID}/Software-Developer?hlkw=python&s=101#apply",
    f"https://www.cv-library.co.uk/job/{JOB_ID}",
    f"http://cv-library.co.uk/job/{JOB_ID}/",
    f"  https://WWW.CV-LIBRARY.CO.UK/job/{JOB_ID}/Dev  ",
])
def test_parse_cvlibrary_url_variants(url):
    assert cvlibrary.parse_cvlibrary_url(url) == (JOB_ID, CANONICAL)


@pytest.mark.parametrize("url", [
    "https://www.indeed.co.uk/viewjob?jk=0123456789abcdef",
    "https://cv-library.co.uk.evil.com/job/123",
    "https://evilcv-library.co.uk/job/123",
    "https://www.cv-library.co.uk/search-jobs",
    "https://www.cv-library.co.uk/job/abc/Dev",
    "https://www.cv-library.co.uk/jobs/123",
    "ftp://www.cv-library.co.uk/job/123",
])
def test_parse_cvlibrary_url_rejects(url):
    with pytest.raises(cvlibrary.NotCVLibraryURLError):
        cvlibrary.parse_cvlibrary_url(url)


def _extracted(**kw):
    return {"company": "Acme", "role": "Engineer", "location": "London",
            "description": "Build things", "salary_min": 50000, "salary_max": 60000, **kw}


def test_import_with_pasted_text_and_duplicate(client, monkeypatch):
    monkeypatch.setattr(ai, "extract_job_from_html", lambda text, url: _extracted())
    body = {"url": f"{CANONICAL}/Software-Developer?s=1", "page_text": "Engineer at Acme ..."}
    r = client.post("/jobs/from-cvlibrary", json=body)
    assert r.status_code == 201, r.text
    job = r.json()
    assert (job["company"], job["role"], job["description"]) == ("Acme", "Engineer", "Build things")
    assert (job["salary_min"], job["salary_max"], job["currency"]) == (50000, 60000, "GBP")
    assert (job["source"], job["platform"], job["status"]) == ("cvlibrary", "CV-Library", "New")
    assert job["source_url"] == CANONICAL

    dup = client.post("/jobs/from-cvlibrary", json={"url": CANONICAL, "page_text": "x"})
    assert dup.status_code == 409
    assert dup.json()["detail"]["job_id"] == job["id"]


def test_import_blocked_asks_for_pasted_text(client, monkeypatch):
    async def blocked(url):
        raise scraper.FetchBlockedError("HTTP 403")
    monkeypatch.setattr(scraper, "fetch_page", blocked)
    r = client.post("/jobs/from-cvlibrary",
                    json={"url": "https://www.cv-library.co.uk/job/987654321"})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "CV-Library" in detail and "paste" in detail.lower()


def test_import_rejects_non_cvlibrary(client):
    r = client.post("/jobs/from-cvlibrary", json={"url": "https://example.com/job/123"})
    assert r.status_code == 400


def test_import_forbidden_in_read_only_mode(client, monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    r = client.post("/jobs/from-cvlibrary", json={"url": CANONICAL, "page_text": "x"})
    assert r.status_code == 403
