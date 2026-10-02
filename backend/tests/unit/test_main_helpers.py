"""Unit tests for pure helpers in app.main."""
import pytest

from app.main import _infer_platform


@pytest.mark.parametrize("url,expected", [
    ("https://www.linkedin.com/jobs/view/123", "LinkedIn"),
    ("https://boards.greenhouse.io/acme/jobs/1", "Greenhouse"),
    ("https://jobs.lever.co/acme/abc", "Lever"),
    ("https://jobs.ashbyhq.com/acme/1", "Ashby"),
    ("https://uk.indeed.com/viewjob?jk=1", "Indeed"),
    ("https://apply.workable.com/acme/j/1", "Workable"),
    ("https://LINKEDIN.COM/JOBS", "LinkedIn"),
    ("https://acme.com/careers/eng", "Direct"),
])
def test_infer_platform(url, expected):
    assert _infer_platform(url) == expected
