"""AI services - all Claude (Anthropic) calls live here.

The user's profile is read from the database (Profile table).

This module was migrated from OpenAI to Anthropic Claude. The public function
signatures and the JSON shapes they return are unchanged, so main.py and the
frontend need no changes.

Claude notes vs OpenAI:
- System prompt is a separate parameter (not a message in the list).
- No strict "JSON mode" flag; we instruct the model to return only JSON and
  strip any stray markdown code fences defensively.
- Anthropic's API is consistent across models, so no quirk-detection needed.
"""
from __future__ import annotations
import json
import re
from typing import Any
from anthropic import Anthropic
from sqlalchemy.orm import Session
from . import models
from .config import settings


_client: Anthropic | None = None


def client() -> Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def render_profile(p: models.Profile | None, include_private: bool = True) -> str:
    """Render the Profile row as markdown for the AI to read."""
    if p is None:
        return "# Profile not yet configured\n\nThe user has not filled in their profile. Treat suitability as low and surface this in the summary."

    parts: list[str] = []

    if p.full_name:
        parts.append(f"# {p.full_name}")
    sub = " · ".join(x for x in [p.headline, p.location] if x)
    if sub:
        parts.append(f"**{sub}**")
    contact = " · ".join(x for x in [p.email, p.phone, p.website, p.linkedin, p.github] if x)
    if contact:
        parts.append(contact)

    if p.summary:
        parts.append("\n## Summary\n" + p.summary)
    if p.experience:
        parts.append("\n## Experience\n" + p.experience)
    if p.skills:
        parts.append("\n## Skills\n" + p.skills)
    if p.education:
        parts.append("\n## Education\n" + p.education)
    if p.achievements:
        parts.append("\n## Achievements\n" + p.achievements)

    if include_private:
        priv = []
        if p.target_roles:    priv.append(f"- **Target roles:** {p.target_roles}")
        if p.target_salary:   priv.append(f"- **Target salary:** {p.target_salary}")
        if p.deal_breakers:   priv.append(f"- **Deal breakers:** {p.deal_breakers}")
        if p.private_notes:   priv.append(f"- **Notes:** {p.private_notes}")
        if priv:
            parts.append("\n## Private notes for the AI (do NOT include in tailored docs)\n" + "\n".join(priv))

    return "\n".join(parts)


def _load_profile(db: Session, include_private: bool = True) -> str:
    return render_profile(db.get(models.Profile, 1), include_private=include_private)


# Strip ```json ... ``` fences that Claude sometimes wraps JSON in.
_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _strip_fences(text: str) -> str:
    text = text.strip()
    m = _FENCE_RE.match(text)
    return m.group(1).strip() if m else text


def _call_json(system: str, user: str, max_output_tokens: int = 4096) -> dict[str, Any]:
    """Call Claude and return the parsed JSON object.

    We append a strict instruction to the system prompt to return only JSON,
    then defensively strip any markdown fences before parsing.
    """
    system_json = system + (
        "\n\nIMPORTANT: Respond with ONLY a single valid JSON object. "
        "No markdown, no code fences, no text before or after the JSON."
    )

    resp = client().messages.create(
        model=settings.anthropic_model,
        max_tokens=max_output_tokens,
        temperature=0.4,
        system=system_json,
        messages=[{"role": "user", "content": user}],
    )

    # Concatenate text blocks (usually just one)
    text = "".join(getattr(b, "text", "") for b in resp.content)
    text = _strip_fences(text) or "{}"

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON: {text[:500]}") from e


# ============================================================================
ANALYSIS_SYSTEM = """You are an expert career coach analyzing job fit for a senior professional.

You will be given the user's profile and a job description. Produce a calibrated, honest analysis. Do not flatter. If the fit is weak, say so.

Respond with a JSON object:
{
  "suitability": <integer 0-100>,
  "summary": "<one sentence top-line on overall fit>",
  "strengths": [{"skill": "...", "level": "Exceeds" or "Match", "note": "..."}],
  "gaps": [{"skill": "...", "note": "..."}],
  "market_salary": {"p25": <int k/year>, "p50": <int>, "p75": <int>, "currency": "<3-letter>", "source": "<source>"},
  "negotiation": {"floor": <int>, "target": <int>, "ceiling": <int>, "rationale": "<one line>"}
}

Calibration: 90+ = strong fit. 75-89 = solid with minor gaps. 60-74 = mixed. <60 = significant misalignment."""


def analyze_job(db: Session, description: str, role: str, company: str, location: str | None) -> dict[str, Any]:
    profile = _load_profile(db, include_private=True)
    user = f"# User profile\n{profile}\n\n# Job\nCompany: {company}\nRole: {role}\nLocation: {location or 'unspecified'}\n\n## Description\n{description}\n"
    return _call_json(ANALYSIS_SYSTEM, user, max_output_tokens=2500)


# ============================================================================
PREP_SYSTEM = """You are a senior interview coach. Generate interview questions tailored to THIS specific role and THIS specific candidate.

Avoid generic questions. Each question should reference something concrete from either the JD or the CV.

Respond with a JSON object:
{
  "technical": [{"q": "...", "why": "...", "framework": "..."}],
  "behavioral": [{"q": "...", "why": "..."}]
}

Generate 4 technical and 4 behavioral. Quality over quantity."""


def generate_prep(db: Session, description: str, role: str, company: str) -> dict[str, Any]:
    profile = _load_profile(db, include_private=True)
    user = f"# User profile\n{profile}\n\n# Job\n{company} - {role}\n\n## Description\n{description}\n"
    return _call_json(PREP_SYSTEM, user, max_output_tokens=3500)


# ============================================================================
RESEARCH_SYSTEM = """You are a research analyst preparing a candidate for an interview.

Be honest about what you know vs. estimate. Do NOT invent specific news items, valuations, or acquisitions.

Respond with a JSON object:
{
  "culture": "<2-3 sentences>",
  "market": "<2-3 sentences>",
  "recent": [{"date": "<approximate>", "item": "<news or 'no specific recent news available'>"}],
  "talking_points": ["<concrete thing to mention>"]
}

3-5 talking points. Be honest if knowledge is limited."""


def research_company(db: Session, company: str, role: str) -> dict[str, Any]:
    user = f"Company: {company}\nRole being interviewed for: {role}"
    return _call_json(RESEARCH_SYSTEM, user, max_output_tokens=1500)


# ============================================================================
TAILOR_SYSTEM = """You are an expert resume writer and career strategist.

Reorder, re-emphasize, and rephrase the user's existing experience to align with what THIS job is asking for. Do not invent experience the user doesn't have. Do not include any private notes/targeting info from their profile in the output.

Respond with a JSON object containing ALL of these keys (use empty arrays if no items):
{
  "content": "<the document in markdown>",
  "ats_match_pct": <integer 0-100>,
  "keywords_matched": ["...", "..."],
  "keywords_missing": ["...", "..."],
  "suggestions": ["...", "..."]
}

You MUST include all five keys in your response, even if some arrays are empty."""


def tailor_doc(db: Session, description: str, role: str, company: str, doc_type: str) -> dict[str, Any]:
    profile = _load_profile(db, include_private=False)
    instructions = {
        "cv": (
            "Generate a tailored CV in markdown using EXACTLY this section order and structure:\n\n"
            "## Professional Summary\n"
            "<3-4 sentences tailored to THIS job, drawing only on the candidate's real background>\n\n"
            "## Core Skills\n"
            "- **<Category>:** <comma-separated skills relevant to this job>\n"
            "<3-6 category lines, most JD-relevant categories first>\n\n"
            "## Certifications\n"
            "- <certification from the profile>\n\n"
            "## Professional Experience\n"
            "### <Job Title> • <Company, Location> @@ <Start - End>\n"
            "- <achievement bullet, reordered and re-emphasised for THIS job's priorities>\n"
            "<include the 3-4 most relevant roles, most recent first; 2-5 bullets each>\n\n"
            "## Education\n"
            "### <Degree> • <Institution> @@ <Start - End>\n\n"
            "## Awards & Achievements\n"
            "- <award from the profile>\n\n"
            "CRITICAL FORMATTING RULES:\n"
            "1. On every Experience and Education heading, put ' @@ ' (space-at-at-space) "
            "between the role/company and the dates. This is required for date alignment.\n"
            "2. Use '•' between job title and company.\n"
            "3. Do NOT output a name/title/contact header - that is added separately.\n"
            "4. Pull every role, date, certification and award from the candidate profile. "
            "Never invent experience, dates, employers, or achievements. You may rephrase and "
            "reorder bullets to match the JD, but the underlying facts must come from the profile."
        ),
        "cover_letter": "Generate a focused cover letter (under 250 words). Open with something specific to the company.",
        "recruiter_email": "Generate a short outreach email (under 150 words). Include subject line.",
    }
    if doc_type not in instructions:
        raise ValueError(f"Unknown doc_type: {doc_type}")
    user = f"# Document type\n{instructions[doc_type]}\n\n# User profile\n{profile}\n\n# Target job\n{company} - {role}\n\n## Description\n{description}\n"
    return _call_json(TAILOR_SYSTEM, user, max_output_tokens=4000)


# ============================================================================
EXTRACT_SYSTEM = """You are a parser. Extract structured fields from a raw job posting.

Respond with a JSON object:
{
  "company": "...",
  "role": "...",
  "location": "<or null>",
  "work_type": "Remote" or "Hybrid" or "Onsite" or null,
  "salary_min": <int k/year or null>,
  "salary_max": <int or null>,
  "currency": "<3-letter or null>",
  "description": "<full description as clean markdown>"
}

Use null where you can't determine. Don't guess salary."""


def extract_job_from_html(html: str, source_url: str) -> dict[str, Any]:
    truncated = html[:50000]
    user = f"Source URL: {source_url}\n\n## Page content\n{truncated}"
    return _call_json(EXTRACT_SYSTEM, user, max_output_tokens=4000)
