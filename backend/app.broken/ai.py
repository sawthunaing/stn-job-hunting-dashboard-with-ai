"""AI services - all OpenAI calls live here.

The user's profile is read from the database (Profile table).
"""
from __future__ import annotations
import json
from typing import Any
from openai import OpenAI
from sqlalchemy.orm import Session
from . import models
from .config import settings


_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def render_profile(p: models.Profile | None, include_private: bool = True) -> str:
    """Render the Profile row as markdown for the AI to read.

    include_private=False omits target salary, deal breakers etc - useful when
    the output goes into a tailored CV/cover letter that recruiters will see.
    """
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


def _call_json(system: str, user: str, max_max_completion_tokens: int = 4096) -> dict[str, Any]:
    resp = client().chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        max_tokens=max_completion_tokens,
        temperature=0.4,
    )
    text = resp.choices[0].message.content or "{}"
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"OpenAI returned non-JSON: {text[:500]}") from e


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
    return _call_json(ANALYSIS_SYSTEM, user, max_tokens=2500)


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
    return _call_json(PREP_SYSTEM, user, max_tokens=3000)


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
    return _call_json(RESEARCH_SYSTEM, user, max_tokens=1500)


# ============================================================================
TAILOR_SYSTEM = """You are an expert resume writer and career strategist.

Reorder, re-emphasize, and rephrase the user's existing experience to align with what THIS job is asking for. Do not invent experience the user doesn't have. Do not include any private notes/targeting info from their profile in the output.

Respond with a JSON object:
{
  "content": "<the document in markdown>",
  "ats_match_pct": <integer 0-100>,
  "keywords_matched": ["..."],
  "keywords_missing": ["..."],
  "suggestions": ["..."]
}"""


def tailor_doc(db: Session, description: str, role: str, company: str, doc_type: str) -> dict[str, Any]:
    # Tailored docs end up in front of recruiters - exclude private notes
    profile = _load_profile(db, include_private=False)
    instructions = {
        "cv": "Generate a tailored CV/resume in markdown. Include summary, key skills, and 3-4 most relevant experience bullets reordered to match this JD's priorities.",
        "cover_letter": "Generate a focused cover letter (under 250 words). Open with something specific to the company.",
        "recruiter_email": "Generate a short outreach email (under 150 words). Include subject line.",
    }
    if doc_type not in instructions:
        raise ValueError(f"Unknown doc_type: {doc_type}")
    user = f"# Document type\n{instructions[doc_type]}\n\n# User profile\n{profile}\n\n# Target job\n{company} - {role}\n\n## Description\n{description}\n"
    return _call_json(TAILOR_SYSTEM, user, max_tokens=2500)


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
    return _call_json(EXTRACT_SYSTEM, user, max_tokens=4000)
