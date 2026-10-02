"""Unit tests for app.ai - prompt building and Claude response parsing.

The Anthropic client is replaced with a fake so no network calls are made.
"""
import json
from types import SimpleNamespace

import pytest

from app import ai, models
from app.config import settings


class FakeMessages:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        texts = self.text if isinstance(self.text, list) else [self.text]
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=t) for t in texts])


@pytest.fixture
def fake_claude(monkeypatch):
    """Returns a factory: fake_claude('{"a": 1}') installs a client replying with that text."""
    def install(text):
        messages = FakeMessages(text)
        monkeypatch.setattr(ai, "client", lambda: SimpleNamespace(messages=messages))
        return messages
    return install


class FakeDB:
    def __init__(self, profile=None):
        self.profile = profile

    def get(self, model, pk):
        assert model is models.Profile and pk == 1
        return self.profile


def make_profile(**overrides):
    data = dict(
        full_name="Jane Doe", headline="Senior Engineer", location="London",
        email="jane@example.com", phone=None, website=None, linkedin="linkedin.com/in/jane", github=None,
        summary="Builds things.", experience="- Acme 2020-2024", skills="Python, AWS",
        education="BSc CS", achievements=None,
        target_roles="Staff Engineer", target_salary="£120k", deal_breakers="No on-site",
        private_notes="Prefers fintech",
    )
    data.update(overrides)
    return models.Profile(**data)


# ---------------------------------------------------------------- client()

class TestClient:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.setattr(ai, "_client", None)
        monkeypatch.setattr(settings, "anthropic_api_key", "")
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            ai.client()

    def test_is_cached(self, monkeypatch):
        monkeypatch.setattr(ai, "_client", None)
        monkeypatch.setattr(settings, "anthropic_api_key", "k")
        assert ai.client() is ai.client()


# ---------------------------------------------------------------- render_profile

class TestRenderProfile:
    def test_none_profile_gives_placeholder(self):
        out = ai.render_profile(None)
        assert "Profile not yet configured" in out

    def test_includes_public_sections_and_skips_empty(self):
        out = ai.render_profile(make_profile(), include_private=False)
        assert out.startswith("# Jane Doe")
        assert "**Senior Engineer · London**" in out
        assert "jane@example.com · linkedin.com/in/jane" in out
        for heading in ("## Summary", "## Experience", "## Skills", "## Education"):
            assert heading in out
        assert "## Achievements" not in out

    def test_private_section_only_when_requested(self):
        with_priv = ai.render_profile(make_profile(), include_private=True)
        without = ai.render_profile(make_profile(), include_private=False)
        assert "Prefers fintech" in with_priv and "£120k" in with_priv
        assert "Private notes" not in without
        assert "Prefers fintech" not in without and "£120k" not in without

    def test_no_private_heading_when_no_private_fields(self):
        p = make_profile(target_roles=None, target_salary=None, deal_breakers=None, private_notes=None)
        assert "Private notes" not in ai.render_profile(p, include_private=True)

    def test_empty_profile_renders_empty_string(self):
        assert ai.render_profile(models.Profile()) == ""


# ---------------------------------------------------------------- _strip_fences

@pytest.mark.parametrize("raw,expected", [
    ('{"a": 1}', '{"a": 1}'),
    ('  {"a": 1}  \n', '{"a": 1}'),
    ('```json\n{"a": 1}\n```', '{"a": 1}'),
    ('```\n{"a": 1}\n```', '{"a": 1}'),
    ('```json{"a": 1}```', '{"a": 1}'),
    ('Here you go: {"a": 1}', 'Here you go: {"a": 1}'),
])
def test_strip_fences(raw, expected):
    assert ai._strip_fences(raw) == expected


# ---------------------------------------------------------------- _call_json

class TestCallJson:
    def test_parses_plain_json(self, fake_claude):
        fake_claude('{"ok": true}')
        assert ai._call_json("sys", "user") == {"ok": True}

    def test_parses_fenced_json(self, fake_claude):
        fake_claude('```json\n{"ok": true}\n```')
        assert ai._call_json("sys", "user") == {"ok": True}

    def test_concatenates_multiple_text_blocks(self, fake_claude):
        fake_claude(['{"a":', ' 1}'])
        assert ai._call_json("sys", "user") == {"a": 1}

    def test_empty_response_is_empty_dict(self, fake_claude):
        fake_claude("")
        assert ai._call_json("sys", "user") == {}

    def test_non_json_raises_value_error(self, fake_claude):
        fake_claude("Sorry, I can't help with that.")
        with pytest.raises(ValueError, match="non-JSON"):
            ai._call_json("sys", "user")

    def test_request_shape(self, fake_claude, monkeypatch):
        monkeypatch.setattr(settings, "anthropic_model", "claude-test-model")
        msgs = fake_claude("{}")
        ai._call_json("SYSTEM PROMPT", "USER PROMPT", max_output_tokens=123)
        call = msgs.calls[0]
        assert call["model"] == "claude-test-model"
        assert call["max_tokens"] == 123
        assert call["system"].startswith("SYSTEM PROMPT")
        assert "ONLY a single valid JSON object" in call["system"]
        assert call["messages"] == [{"role": "user", "content": "USER PROMPT"}]


# ---------------------------------------------------------------- public AI functions

class TestAiFunctions:
    def test_analyze_job_uses_private_profile(self, fake_claude):
        msgs = fake_claude(json.dumps({"suitability": 80}))
        out = ai.analyze_job(FakeDB(make_profile()), "Build APIs", "Engineer", "Acme", None)
        assert out == {"suitability": 80}
        user = msgs.calls[0]["messages"][0]["content"]
        assert "Company: Acme" in user and "Role: Engineer" in user
        assert "Location: unspecified" in user
        assert "Build APIs" in user
        assert "Prefers fintech" in user
        assert msgs.calls[0]["system"].startswith(ai.ANALYSIS_SYSTEM)

    def test_generate_prep(self, fake_claude):
        msgs = fake_claude('{"technical": [], "behavioral": []}')
        out = ai.generate_prep(FakeDB(None), "desc", "Engineer", "Acme")
        assert out == {"technical": [], "behavioral": []}
        assert "Acme - Engineer" in msgs.calls[0]["messages"][0]["content"]

    def test_research_company_does_not_send_profile(self, fake_claude):
        msgs = fake_claude('{"culture": "x"}')
        ai.research_company(FakeDB(make_profile()), "Acme", "Engineer")
        user = msgs.calls[0]["messages"][0]["content"]
        assert user == "Company: Acme\nRole being interviewed for: Engineer"

    @pytest.mark.parametrize("doc_type,marker", [
        ("cv", "## Professional Summary"),
        ("cover_letter", "cover letter"),
        ("recruiter_email", "outreach email"),
    ])
    def test_tailor_doc_never_leaks_private_notes(self, fake_claude, doc_type, marker):
        msgs = fake_claude('{"content": "doc"}')
        out = ai.tailor_doc(FakeDB(make_profile()), "desc", "Engineer", "Acme", doc_type)
        assert out == {"content": "doc"}
        user = msgs.calls[0]["messages"][0]["content"]
        assert marker in user
        assert "Prefers fintech" not in user and "£120k" not in user

    def test_tailor_doc_rejects_unknown_type(self, fake_claude):
        msgs = fake_claude("{}")
        with pytest.raises(ValueError, match="Unknown doc_type"):
            ai.tailor_doc(FakeDB(None), "d", "r", "c", "haiku")
        assert msgs.calls == []

    def test_extract_job_truncates_page(self, fake_claude):
        msgs = fake_claude('{"company": "Acme"}')
        out = ai.extract_job_from_html("Z" * 60000, "https://example.com/job")
        assert out == {"company": "Acme"}
        user = msgs.calls[0]["messages"][0]["content"]
        assert "Source URL: https://example.com/job" in user
        assert user.count("Z") == 50000
