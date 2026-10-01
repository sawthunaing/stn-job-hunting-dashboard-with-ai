"""Fetch a job posting URL and return cleaned text for AI extraction.

Fetching is SSRF-hardened: only http(s) to public IP addresses, redirects are
followed manually and re-validated at every hop, and the body size is capped.
"""
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_REDIRECTS = 5
MAX_BYTES = 2_000_000


class UnsafeURLError(ValueError):
    """The URL points somewhere the server must not fetch."""


class FetchBlockedError(Exception):
    """The remote site refused or challenged the request (bot protection)."""


def _resolve_public(host: str, port: int) -> None:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise UnsafeURLError(f"cannot resolve host: {host}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise UnsafeURLError("URL resolves to a non-public address")


def validate_public_url(url: str) -> str:
    """Return the URL if it is http(s) to a public host, else raise UnsafeURLError.

    The host is resolved here and again by httpx at connect time, so a DNS
    rebinding attacker could still win the race; the egress firewall is the
    real backstop for that.
    """
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https"):
        raise UnsafeURLError("only http and https URLs are allowed")
    if not parts.hostname:
        raise UnsafeURLError("URL has no host")
    if parts.username or parts.password:
        raise UnsafeURLError("URLs with credentials are not allowed")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    _resolve_public(parts.hostname, port)
    return url.strip()


async def _get_validated(client: httpx.AsyncClient, url: str) -> str:
    """GET url, following redirects manually with validation; return the HTML."""
    for _ in range(MAX_REDIRECTS + 1):
        validate_public_url(url)
        async with client.stream("GET", url) as r:
            if r.is_redirect:
                loc = r.headers.get("location")
                if not loc:
                    raise httpx.HTTPError("redirect without location")
                url = urljoin(url, loc)
                continue
            if r.status_code in (403, 429, 503):
                raise FetchBlockedError(f"site returned HTTP {r.status_code}")
            r.raise_for_status()
            chunks: list[bytes] = []
            size = 0
            async for chunk in r.aiter_bytes():
                size += len(chunk)
                if size > MAX_BYTES:
                    break
                chunks.append(chunk)
            return b"".join(chunks).decode(r.encoding or "utf-8", errors="replace")
    raise httpx.TooManyRedirects("too many redirects")


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator="\n", strip=True)
    lines = [ln for ln in (l.strip() for l in text.splitlines()) if ln]
    return "\n".join(lines)


async def fetch_page(url: str) -> str:
    """Fetch URL, strip script/style, return readable text."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=False) as c:
        html = await _get_validated(c, url)
    return html_to_text(html)
