import pytest

from app import scraper


@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data/",
    "http://127.0.0.1:8000/",
    "http://localhost/",
    "http://[::1]/",
    "http://10.0.0.5/",
    "file:///etc/passwd",
    "http://user:pw@example.com/",
])
def test_rejects_unsafe_urls(url):
    with pytest.raises(scraper.UnsafeURLError):
        scraper.validate_public_url(url)


def test_accepts_public_ip():
    assert scraper.validate_public_url("https://1.1.1.1/") == "https://1.1.1.1/"
