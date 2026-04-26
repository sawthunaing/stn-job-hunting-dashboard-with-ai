"""Fetch a job posting URL and return cleaned text for AI extraction."""
import httpx
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_page(url: str) -> str:
    """Fetch URL, strip script/style, return readable text."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as c:
        r = await c.get(url)
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = main.get_text(separator="\n", strip=True)
    lines = [ln for ln in (l.strip() for l in text.splitlines()) if ln]
    return "\n".join(lines)
