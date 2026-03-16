"""
Remotive source: fetch jobs from https://remotive.com/api/remote-jobs and map each job to a company.
Contract: name, nit, email, phone, url, country, sector, technologies, source, source_url.
MVP: max 100 items per run.
"""

import requests
from typing import Any

USER_AGENT = "Sclapp/1.0 (scraping; +https://github.com/sclapp)"
MAX_ITEMS = 100
API_URL = "https://remotive.com/api/remote-jobs"


def scrape() -> list[dict[str, Any]]:
    """
    Fetch Remotive API and return a list of company dicts (one per job).
    Maps: company_name -> name, url -> url, category -> sector, technologies = tags when available.
    """
    resp = requests.get(
        API_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    jobs = data.get("jobs") if isinstance(data, dict) else []
    if not isinstance(jobs, list):
        return []

    companies: list[dict[str, Any]] = []
    for job in jobs:
        if len(companies) >= MAX_ITEMS:
            break
        if not isinstance(job, dict):
            continue
        name = (job.get("company_name") or "").strip()
        if not name:
            continue
        url = job.get("url")
        if isinstance(url, str):
            url = url.strip() or None
        else:
            url = None
        category = job.get("category")
        sector = (category.strip() if isinstance(category, str) and category.strip() else "Technology") or "Technology"
        technologies = [category] if isinstance(category, str) and category.strip() else []
        tags = job.get("tags")
        if isinstance(tags, list):
            technologies = [str(t).strip() for t in tags if t][:20]
        job_title = (job.get("title") or "").strip() or None
        job_category = (category.strip() if isinstance(category, str) and category.strip() else None) or None
        job_description = job.get("description")
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
            "sector": sector,
            "technologies": technologies,
            "source": "remotive",
            "source_url": url or "https://remotive.com/",
            "job_title": job_title,
            "job_category": job_category,
            "job_description": job_description,
        })
    return companies
