"""
Normalizer for scraping data.

Provides company name normalization, URL domain extraction, and a deduplication
key so the same company is not inserted twice (by NIT, domain, or country+name).
"""

from typing import Any, Dict, Optional
import re
import unicodedata
from urllib.parse import urlparse


def normalize_name(name: Optional[str]) -> str:
    """
    Normalize a company name:
    - Convert to string and lowercase.
    - Remove diacritics/accents by Unicode normalization and ASCII transliteration.
    - Keep only ASCII letters (a-z), digits (0-9) and spaces.
    - Collapse multiple spaces and strip edges.

    Returns an empty string for falsy input.
    """
    if not name:
        return ""
    s = str(name)
    # Decompose and remove diacritics, then drop any remaining non-ascii
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    # Keep letters, digits and spaces only
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    # Collapse whitespace and trim
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_domain(url: Optional[str]) -> Optional[str]:
    """
    Extract the domain (host) from a URL.
    - Accepts URLs with or without scheme.
    - Removes credentials (user:pass@), ports and 'www.' prefix.
    - Returns lowercased domain (e.g. 'example.com') or None if not found.
    """
    if not url:
        return None
    u = str(url).strip()
    if not u:
        return None
    # Ensure a scheme so urlparse places the host in netloc
    if "://" not in u:
        u = "http://" + u
    parsed = urlparse(u)
    netloc = parsed.netloc or ""
    if not netloc:
        return None
    # Remove credentials and port
    if "@" in netloc:
        netloc = netloc.split("@", 1)[1]
    netloc = netloc.split(":", 1)[0]
    netloc = netloc.lower().strip()
    # Remove leading www.
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc or None


def generate_dedupe_key(company: Dict[str, Any]) -> str:
    """
    Generate a deduplication key for a company dict.

    Rules (priority order):
      1) If 'nit' exists -> return digits-only normalized NIT (e.g. '12345678').
      2) Else -> return '<normalized_name>|<domain>' if domain is available.
      3) Else -> return '<normalized_name>|<country>' if country is available (lowercased).
      4) Fallback -> return normalized_name (may be empty string).

    The function accepts common alternative keys for input:
      - NIT: 'nit'
      - Name: 'name', 'nombre'
      - URL: 'url', 'website', 'site'
      - Country: 'country', 'pais', 'país'
    """
    # 1) NIT (digits-only)
    nit = company.get("nit") or company.get("NIT")
    if nit is not None:
        nit_digits = re.sub(r"\D", "", str(nit))
        if nit_digits:
            return nit_digits

    # Name normalization
    name = company.get("name") or company.get("nombre") or ""
    normalized_name = normalize_name(name)

    # 2) Domain from URL
    url = company.get("url") or company.get("website") or company.get("site")
    domain = extract_domain(url) if url else None
    if domain:
        return f"{normalized_name}|{domain}"

    # 3) Country fallback
    country = (
        company.get("country")
        or company.get("pais")
        or company.get("país")
        or company.get("Country")
    )
    if country:
        country_norm = str(country).strip().lower()
        return f"{normalized_name}|{country_norm}"

    # 4) Final fallback: normalized name (may be empty)
    return normalized_name
