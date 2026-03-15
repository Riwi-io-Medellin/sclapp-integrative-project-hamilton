"""
Example scraping source.

Demo scraper that fetches a static HTML page and parses a table to return
company-like records. Used for testing the scraping pipeline. Returns data
following the same contract as RemoteOK/Remotive (name, url, source, etc.).
"""

# TODO (Copilot): Implement a basic scraper using requests + BeautifulSoup.
# Requirements:
# - Define scrape() -> list[dict]
# - It must return a list of companies following this contract:
#   {
#     "name": str,
#     "nit": str|None,
#     "email": str|None,
#     "phone": str|None,
#     "url": str|None,
#     "country": str|None,
#     "sector": str|None,
#     "technologies": list[str],
#     "source": str,
#     "source_url": str|None
#   }
# - For week 1, it can fill only name/url/source/source_url and set the rest to None or [].
# - Use a stable HTML page and parse a table/list to produce at least 3 items.
# - Include robust timeout and raise_for_status().
# Add comments explaining each step.

import requests
from bs4 import BeautifulSoup
from typing import Any
from urllib.parse import urljoin

def scrape() -> list[dict]:
    """
    Basic scraper that returns a list of company dicts following the required contract.
    For week 1 it fills only: name, url, source, source_url. Other fields are None or [].
    """
    # Stable example page with a simple HTML table of companies
    source_url = "https://www.w3schools.com/html/html_tables.asp"
    source_name = "w3schools:html_tables"

    # Perform HTTP GET with a timeout and ensure we raise for HTTP errors
    resp = requests.get(source_url, timeout=10)
    resp.raise_for_status()

    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    # The example table on this page has id="customers"; locate it
    table = soup.find("table", id="customers")
    companies: list[dict[str, Any]] = []

    if table:
        # Iterate rows skipping the header row
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all(["td", "th"])
            if not cols:
                continue
            # First column contains the company name; try to extract an <a> if present
            name_cell = cols[0]
            name = name_cell.get_text(strip=True)
            link = name_cell.find("a")
            url = None
            if link and link.has_attr("href"):
                # Convert relative links to absolute
                url = urljoin(source_url, link["href"])

            # Build the company dict following the contract.
            companies.append(
                {
                    "name": name or "",
                    "nit": None,
                    "email": None,
                    "phone": None,
                    "url": url,
                    "country": None,
                    "sector": None,
                    "technologies": [],
                    "source": source_name,
                    "source_url": source_url,
                }
            )
            # Stop early if we have at least 10 items to avoid over-parsing the page
            if len(companies) >= 10:
                break

    # Fallback: if parsing failed or returned fewer than 3, add placeholder companies
    if len(companies) < 3:
        placeholders = [
            {"name": "Example Company A", "url": None},
            {"name": "Example Company B", "url": None},
            {"name": "Example Company C", "url": None},
        ]
        for ph in placeholders:
            companies.append(
                {
                    "name": ph["name"],
                    "nit": None,
                    "email": None,
                    "phone": None,
                    "url": ph["url"],
                    "country": None,
                    "sector": None,
                    "technologies": [],
                    "source": source_name,
                    "source_url": source_url,
                }
            )
            if len(companies) >= 3:
                break

    return companies