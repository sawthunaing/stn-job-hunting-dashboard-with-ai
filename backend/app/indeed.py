"""Helpers for importing job postings from Indeed.

Indeed has no job-seeker API and challenges server-side requests with bot
protection, so the import accepts either the posting URL alone (best-effort
fetch) or the URL plus text the user copied from their own browser.
"""
import re
from urllib.parse import parse_qs, urlsplit

SOURCE = "indeed"

_HOST_RE = re.compile(r"(^|\.)indeed\.[a-z]{2,3}(\.[a-z]{2})?$")
_JOB_KEY_RE = re.compile(r"^[0-9a-f]{16}$")


class NotIndeedURLError(ValueError):
    pass


def parse_indeed_url(url: str) -> tuple[str, str]:
    """Return (job_key, canonical_url) for an Indeed posting URL.

    Accepts viewjob / search-result URLs carrying a `jk` or `vjk` parameter on
    any Indeed country domain. Raises NotIndeedURLError otherwise.
    """
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not _HOST_RE.search(host):
        raise NotIndeedURLError("Not an Indeed URL")
    query = parse_qs(parts.query)
    key = (query.get("jk") or query.get("vjk") or [""])[0].lower()
    if not _JOB_KEY_RE.match(key):
        raise NotIndeedURLError("Could not find a job id (jk) in the Indeed URL")
    return key, f"https://{host}/viewjob?jk={key}"


def looks_like_challenge(text: str) -> bool:
    """True if fetched text is a bot-protection page rather than a posting."""
    t = text.lower()
    return len(t) < 400 and any(
        s in t for s in ("captcha", "just a moment", "verify you are human", "access denied")
    )
