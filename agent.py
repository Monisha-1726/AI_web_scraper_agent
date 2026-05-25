"""
agent.py — Web Scraper using httpx + BeautifulSoup + Groq LLM
100% FREE | No browser-use | No Playwright | Works everywhere
"""

import json
import re
import logging

import httpx
from bs4 import BeautifulSoup
from groq import Groq

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

MOBILE_HEADERS = {
    **HEADERS,
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
}


async def run_scrape_agent(url: str, query: str, api_key: str) -> list[dict]:
    """
    Main entry point:
    1. Fetch page with httpx
    2. Extract clean text with BeautifulSoup
    3. Send to Groq LLM for structured extraction
    """
    # Step 1: Fetch
    html = await _fetch_page(url)
    if html is None:
        return [{"error": f"Could not fetch page", "url": url,
                 "tip": "Check URL or internet connection"}]

    # Step 2: Extract clean text
    page_text = _extract_text(html, url)
    if not page_text.strip():
        return [{"error": "Page has no readable text", "url": url}]

    # Step 3: Groq extraction
    return await _groq_extract(url, page_text, query, api_key)


async def _fetch_page(url: str) -> str | None:
    """Try fetching with desktop UA, fallback to mobile UA."""
    for headers in [HEADERS, MOBILE_HEADERS]:
        try:
            async with httpx.AsyncClient(
                headers=headers,
                follow_redirects=True,
                timeout=30,
                verify=False,
            ) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    logger.info(f"[fetch] OK {url}")
                    return resp.text
                logger.warning(f"[fetch] Status {resp.status_code} for {url}")
        except Exception as e:
            logger.warning(f"[fetch] Failed: {e}")
    return None


def _extract_text(html: str, url: str) -> str:
    """Extract clean structured text from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "noscript", "header",
                     "footer", "nav", "iframe", "meta", "link"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    parts = []

    # Headings
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        t = tag.get_text(separator=" ", strip=True)
        if t:
            parts.append(f"[HEADING] {t}")

    # Tables
    for table in soup.find_all("table"):
        rows = []
        for row in table.find_all("tr"):
            cells = [
                td.get_text(separator=" ", strip=True)
                for td in row.find_all(["td", "th"])
            ]
            if any(cells):
                rows.append(" | ".join(cells))
        if rows:
            parts.append("[TABLE]\n" + "\n".join(rows))

    # Lists
    for tag in soup.find_all("li"):
        t = tag.get_text(separator=" ", strip=True)
        if len(t) > 10:
            parts.append(f"• {t}")

    # Paragraphs & other text
    for tag in soup.find_all(["p", "span", "div", "a", "td"]):
        t = tag.get_text(separator=" ", strip=True)
        if len(t) > 30:
            parts.append(t)

    # Deduplicate
    seen = set()
    unique = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    full = f"PAGE TITLE: {title}\nURL: {url}\n\n" + "\n".join(unique)
    return full[:15000]


async def _groq_extract(url: str, page_text: str, query: str, api_key: str) -> list[dict]:
    """Send page text to Groq Llama and get structured JSON back."""
    client = Groq(api_key=api_key)

    prompt = f"""You are a data extraction expert. Extract structured data from this webpage.

TASK: {query}
SOURCE: {url}

WEBPAGE CONTENT:
{page_text[:12000]}

RULES:
- Extract ONLY what was asked in TASK
- Return a valid JSON array of objects with snake_case keys
- Each object = one record (one product, one post, one item, etc.)
- NO markdown, NO explanation, NO code fences
- Just the raw JSON array

Good output example:
[{{"title": "Book Name", "price": "£12.99", "rating": "4 stars"}}]

If nothing relevant found:
[{{"error": "no relevant data found", "reason": "brief explanation"}}]
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        logger.info(f"[groq] extracted {len(raw)} chars")
        return _parse_json(raw)
    except Exception as e:
        logger.error(f"[groq] failed: {e}")
        return [{"error": f"Groq extraction failed: {str(e)}"}]


def _parse_json(text: str) -> list[dict]:
    """Robustly parse a JSON array from LLM output."""
    if not text:
        return [{"error": "Empty response from LLM"}]

    # Strip markdown fences
    clean = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()

    # Direct parse
    try:
        data = json.loads(clean)
        if isinstance(data, list):
            return data if data else [{"error": "Empty list returned"}]
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list) and v:
                    return v
        return [data]
    except json.JSONDecodeError:
        pass

    # Find largest [...] block
    for m in reversed(list(re.finditer(r"\[", clean))):
        start = m.start()
        depth = 0
        for i, ch in enumerate(clean[start:], start):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    candidate = clean[start: i + 1]
                    try:
                        data = json.loads(candidate)
                        if isinstance(data, list) and data:
                            return data
                    except json.JSONDecodeError:
                        break

    return [{"raw_output": text[:2000]}]
