"""Unit tests for app.scraper.fetch_page (HTTP is mocked with httpx.MockTransport)."""
import asyncio

import httpx
import pytest

from app import scraper


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def mock_http(monkeypatch):
    """mock_http(handler) routes every httpx.AsyncClient request through handler."""
    real_client = httpx.AsyncClient

    def install(handler):
        def factory(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return real_client(*args, **kwargs)
        monkeypatch.setattr(scraper.httpx, "AsyncClient", factory)
    return install


PAGE = """
<html><head><title>T</title><style>.x{color:red}</style></head>
<body>
  <header>Site header</header>
  <nav>Home | Jobs</nav>
  <main>
    <h1>Senior Engineer</h1>
    <script>track()</script>
    <p>  Acme Ltd  </p>

    <p>Build great things.</p>
    <svg><text>icon</text></svg>
  </main>
  <footer>© Acme</footer>
</body></html>
"""


def test_extracts_main_text_and_strips_noise(mock_http):
    mock_http(lambda req: httpx.Response(200, text=PAGE))
    text = run(scraper.fetch_page("https://example.com/job"))
    assert text == "Senior Engineer\nAcme Ltd\nBuild great things."


def test_sends_browser_like_headers(mock_http):
    seen = {}

    def handler(req):
        seen.update(req.headers)
        return httpx.Response(200, text="<p>x</p>")

    mock_http(handler)
    run(scraper.fetch_page("https://example.com"))
    assert "Mozilla" in seen["user-agent"]


def test_falls_back_to_article_then_body(mock_http):
    mock_http(lambda req: httpx.Response(200, text="<body><div>Outside</div><article>Inside</article></body>"))
    assert run(scraper.fetch_page("https://e.com")) == "Inside"

    mock_http(lambda req: httpx.Response(200, text="<body><div>Only body</div></body>"))
    assert run(scraper.fetch_page("https://e.com")) == "Only body"


def test_follows_redirects(mock_http):
    def handler(req):
        if req.url.path == "/old":
            return httpx.Response(301, headers={"Location": "https://e.com/new"})
        return httpx.Response(200, text="<main>Moved here</main>")

    mock_http(handler)
    assert run(scraper.fetch_page("https://e.com/old")) == "Moved here"


def test_http_error_raises(mock_http):
    mock_http(lambda req: httpx.Response(403, text="blocked"))
    with pytest.raises(httpx.HTTPStatusError):
        run(scraper.fetch_page("https://linkedin.com/jobs/1"))
