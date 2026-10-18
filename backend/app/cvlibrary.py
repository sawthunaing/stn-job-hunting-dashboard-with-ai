"""Helpers for importing job postings from CV-Library.

Like Indeed, CV-Library has no job-seeker API, so the import accepts either the
posting URL alone (best-effort fetch) or the URL plus text the user copied from
their own browser.
"""
import re
from urllib.parse import urlsplit

SOURCE = "cvlibrary"
CANONICAL_HOST = "www.cv-library.co.uk"

_HOST_RE = re.compile(r"^(www\.)?cv-library\.co\.uk$")
_JOB_PATH_RE = re.compile(r"^/job/(\d+)(/|$)")


class NotCVLibraryURLError(ValueError):
    pass


def parse_cvlibrary_url(url: str) -> tuple[str, str]:
    """Return (job_id, canonical_url) for a CV-Library posting URL.

    Accepts `/job/<digits>` URLs with or without the trailing title slug.
    Raises NotCVLibraryURLError otherwise.
    """
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not _HOST_RE.match(host):
        raise NotCVLibraryURLError("Not a CV-Library URL")
    m = _JOB_PATH_RE.match(parts.path)
    if not m:
        raise NotCVLibraryURLError("Could not find a job id in the CV-Library URL")
    job_id = m.group(1)
    return job_id, f"https://{CANONICAL_HOST}/job/{job_id}"
