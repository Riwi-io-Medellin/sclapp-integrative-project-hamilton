"""
RemoteOK source: fetch jobs from https://remoteok.com/api and map each job to a company.
Contract: name, nit, email, phone, url, country, sector, technologies, source, source_url.
MVP: max 30 items per run.
"""

import requests
from typing import Any

USER_AGENT = "Sclapp/1.0 (scraping; +https://github.com/sclapp)"
MAX_ITEMS = 30
API_URL = "https://remoteok.com/api"


def scrape() -> list[dict[str, Any]]:
    """
    Fetch RemoteOK API and return a list of company dicts (one per job).
    Maps: company -> name, url -> url, tags -> technologies, country=Global, sector=Technology.
    """
    resp = requests.get(
        API_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if not isinstance(data, list):
        return []

    companies: list[dict[str, Any]] = []
    for item in data:
        if len(companies) >= MAX_ITEMS:
            break
        if not isinstance(item, dict) or "company" not in item:
            continue
        name = (item.get("company") or "").strip()
        if not name:
            continue
        url = item.get("url")
        if isinstance(url, str):
            url = url.strip() or None
        else:
            url = None
        tags = item.get("tags")
        if isinstance(tags, list):
            technologies = [str(t).strip() for t in tags if t]
        else:
            technologies = []
        job_title = (item.get("position") or "").strip() or None
        job_description = item.get("description")
        if isinstance(job_description, str):
            job_description = job_description.strip() or None
        else:
            job_description = None

        companies.append({
            "name": name,
            "nit": None,
            "email": None,
            "phone": None,
            "url": url,
            "country": "Global",
            "sector": "Technology",
            "technologies": technologies[:20],
            "source": "remoteok",
            "source_url": "https://remoteok.com/",
            "job_title": job_title,
            "job_category": "Technology",
            "job_description": job_description,
        })
    return companies
