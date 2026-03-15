"""

FUTURE IMPLEMENTATION: this source is not working yet, but we will implement it in the future.

GetOnBoard source: scrape https://www.getonbrd.com/empleos (jobs listing) and extract companies.
Uses requests + BeautifulSoup. Contract: name, nit, email, phone, url, country, sector, technologies, source, source_url.
MVP: max 30 items per run.
"""

import requests
from bs4 import BeautifulSoup
from typing import Any
from urllib.parse import urljoin

USER_AGENT = "Sclapp/1.0 (scraping; +https://github.com/sclapp)"
MAX_ITEMS = 30
BASE_URL = "https://www.getonbrd.com"
JOBS_URL = "https://www.getonbrd.com/empleos"


def scrape() -> list[dict[str, Any]]:
    """
    Fetch GetOnBoard jobs page and parse HTML to extract company name and link per job.
    Maps: extracted name -> name, link -> url, country=Global, sector=Technology, technologies=[].
    """
    resp = requests.get(
        JOBS_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    companies: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    # Try common listing patterns: job cards often have company name in a link or specific class
    # Selectors to try (in order): data attributes, common classes, semantic tags
    candidates = (
        soup.select("[data-company], .gb-results-list__company, .company-name, .job-card__company, .company, [class*='company']")
        or soup.select("article a[href*='/empresas/'], .gb-results-list__item a")
        or soup.find_all("a", href=lambda h: h and "/empresas/" in h)
    )
    if not candidates:
        # Fallback: any link to /empresas/ (company profile)
        candidates = soup.find_all("a", href=lambda h: h and "/empresas/" in str(h))

    for node in candidates:
        if len(companies) >= MAX_ITEMS:
            break
        name = None
        url = None
        if hasattr(node, "get"):
            name = node.get("data-company") or (node.get("aria-label") and str(node.get("aria-label")).strip())
        if hasattr(node, "get") and node.get("href"):
            url = urljoin(BASE_URL, node["href"])
        if not name and hasattr(node, "get_text"):
            name = node.get_text(strip=True)
        if not name and hasattr(node, "string") and node.string:
            name = node.string.strip() if isinstance(node.string, str) else None
        if not name or not isinstance(name, str):
            continue
        name = name.strip()
        if len(name) < 2 or len(name) > 200:
            continue
        if name.lower() in seen_names:
            continue
        seen_names.add(name.lower())
        companies.append({
            "name": name,
            "nit": None,
            "email": None,
            "phone": None,
            "url": url,
            "country": "Global",
            "sector": "Technology",
            "technologies": [],
            "source": "getonboard",
            "source_url": JOBS_URL,
        })

    return companies
