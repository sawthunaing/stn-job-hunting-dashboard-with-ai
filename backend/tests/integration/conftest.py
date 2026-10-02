"""Fixtures for integration tests: the real FastAPI app wired to a real SQLite DB.

Only the external boundaries are faked - the Anthropic API (app.ai._call_json)
and outbound HTTP (app.scraper.fetch_page). Everything else (routing, auth,
validation, ORM, serialization) runs for real.
"""
import pytest
from fastapi.testclient import TestClient

from app import ai, scraper
from app.db import engine
from app.main import app
from app.models import Base

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # runs the startup hook -> init_db()
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def token(client):
    r = client.post("/auth/login", json={"username": "tester", "password": "s3cret-test-password"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fake_claude(monkeypatch):
    """Route every Claude call to canned responses keyed by system prompt.

    Returns the list of (system, user) prompts the app sent so tests can
    assert on what reached the model.
    """
    responses = {
        ai.ANALYSIS_SYSTEM: {
            "suitability": 82,
            "summary": "Strong fit.",
            "strengths": [{"skill": "Python", "level": "Exceeds", "note": "10y"}],
            "gaps": [{"skill": "Kubernetes", "note": "limited"}],
            "market_salary": {"p25": 80, "p50": 95, "p75": 110, "currency": "GBP", "source": "est"},
            "negotiation": {"floor": 90, "target": 100, "ceiling": 115, "rationale": "market"},
        },
        ai.PREP_SYSTEM: {
            "technical": [{"q": "Design a queue", "why": "JD", "framework": "STAR"}],
            "behavioral": [{"q": "Tell me about a conflict", "why": "CV"}],
        },
        ai.RESEARCH_SYSTEM: {
            "culture": "Collaborative.", "market": "Growing.",
            "recent": [{"date": "2025", "item": "no specific recent news available"}],
            "talking_points": ["Scale"],
        },
        ai.TAILOR_SYSTEM: {
            "content": "## Professional Summary\nTailored.",
            "ats_match_pct": 77, "keywords_matched": ["Python"],
            "keywords_missing": ["Go"], "suggestions": ["Add metrics"],
        },
        ai.EXTRACT_SYSTEM: {
            "company": "Acme", "role": "Backend Engineer", "location": "London",
            "work_type": "Hybrid", "salary_min": 70, "salary_max": 90, "currency": None,
            "description": "Build APIs in Python.",
        },
    }
    calls = []

    def fake_call_json(system, user, max_output_tokens=4096):
        calls.append((system, user))
        return dict(responses[system])

    monkeypatch.setattr(ai, "_call_json", fake_call_json)
    return calls


@pytest.fixture
def fake_fetch(monkeypatch):
    fetched = []

    async def fake_fetch_page(url):
        fetched.append(url)
        return "Backend Engineer at Acme. Build APIs in Python."

    monkeypatch.setattr(scraper, "fetch_page", fake_fetch_page)
    return fetched
