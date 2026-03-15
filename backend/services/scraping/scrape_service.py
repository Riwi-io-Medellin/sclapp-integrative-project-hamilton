"""
Scraping service.

This module coordinates the scraping process: it calls the selected job source
(RemoteOK, Remotive, or example), normalizes company data, filters jobs by
Riwi relevance, runs AI classification when available, and persists results
to PostgreSQL (company, technologies, company_technologies, scraping_logs).
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.db.connection import execute_query, get_db_info
from . import normalizer
from . import job_filters
from backend.services.ai import job_classifier
from .sources import example_source
from .sources import remoteok
from .sources import remotive

SCRAPERS = {
    "example_source": example_source.scrape,
    "remoteok": remoteok.scrape,
    "remotive": remotive.scrape,
}


def _safe_company_contract(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the company dict contains all required keys with safe defaults.
    Contract: name, nit, email, phone, url, country, sector, technologies, source, source_url.
    """
    return {
        "name": str(raw.get("name") or ""),
        "nit": raw.get("nit"),
        "email": raw.get("email"),
        "phone": raw.get("phone"),
        "url": raw.get("url"),
        "country": raw.get("country"),
        "sector": raw.get("sector"),
        "technologies": list(raw.get("technologies") or []),
        "source": str(raw.get("source") or ""),
        "source_url": raw.get("source_url"),
    }


def _normalize_nit(nit: Optional[str]) -> Optional[str]:
    """Return digits-only NIT or None if empty."""
    if nit is None:
        return None
    digits = re.sub(r"\D", "", str(nit))
    return digits if digits else None


def normalize_technology_name(name: str) -> str:
    """Normalize tech name for technologies.name_normalization: lower, strip, collapse spaces."""
    if not name or not isinstance(name, str):
        return ""
    return re.sub(r"\s+", " ", name.strip().lower()).strip()


def upsert_technology(name: str) -> Optional[int]:
    """
    Insert technology if not exists (by name_normalization), return id_tech.
    Uses ON CONFLICT DO NOTHING and then SELECT to get id_tech.
    """
    norm = normalize_technology_name(name)
    if not norm:
        return None
    display_name = (name.strip() or norm)[:100]
    execute_query(
        """
        INSERT INTO technologies (name_tech, name_normalization)
        VALUES (%s, %s)
        ON CONFLICT (name_normalization) DO NOTHING
        """,
        (display_name, norm),
        fetch=False,
    )
    rows = execute_query(
        "SELECT id_tech FROM technologies WHERE name_normalization = %s LIMIT 1",
        (norm,),
    )
    if rows and len(rows) > 0:
        return int(rows[0]["id_tech"])
    return None


def link_company_technology(id_company: int, id_tech: int) -> None:
    """Insert company_technologies if not exists (no duplicate relations)."""
    execute_query(
        """
        INSERT INTO company_technologies (id_company, id_tech)
        VALUES (%s, %s)
        ON CONFLICT (id_company, id_tech) DO NOTHING
        """,
        (id_company, id_tech),
        fetch=False,
    )


def find_existing_company(
    nit: Optional[str],
    country: Optional[str],
    name_normalization: str,
) -> Optional[Dict[str, Any]]:
    """
    Find an existing company by nit if present, else by (country, name_normalization).
    Returns first row as dict or None.
    """
    nit_clean = _normalize_nit(nit) if nit else None
    if nit_clean:
        rows = execute_query(
            "SELECT * FROM company WHERE nit = %s LIMIT 1",
            (nit_clean,),
        )
        if rows and len(rows) > 0:
            return dict(rows[0])

    country_val = (country or "").strip() or None
    if country_val is not None:
        rows = execute_query(
            "SELECT * FROM company WHERE country = %s AND name_normalization = %s LIMIT 1",
            (country_val, name_normalization),
        )
    else:
        rows = execute_query(
            "SELECT * FROM company WHERE (country IS NULL OR trim(coalesce(country, '')) = '') AND name_normalization = %s LIMIT 1",
            (name_normalization,),
        )
    if rows and len(rows) > 0:
        return dict(rows[0])
    return None


def insert_company(
    nit: Optional[str],
    name: str,
    name_normalization: str,
    sector: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    url: Optional[str],
    country: Optional[str],
    description: Optional[str] = None,
    category: Optional[str] = None,
    score: Optional[int] = None,
) -> Optional[int]:
    """Insert a new company. id_status set by DB trigger. Returns id_company or None."""
    if score is not None and (score < 1 or score > 3):
        score = None
    rows = execute_query(
        """
        INSERT INTO company (nit, name, name_normalization, sector, email, phone, url, country, description, category, score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id_company
        """,
        (
            nit or None,
            name or "",
            name_normalization,
            sector or None,
            email or None,
            phone or None,
            url or None,
            (country or "").strip() or None,
            description or None,
            (category or "").strip() or None,
            score,
        ),
        fetch=True,
    )
    if rows and len(rows) > 0:
        return int(rows[0]["id_company"])
    return None


def update_company(
    id_company: int,
    existing: Dict[str, Any],
    sector: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    url: Optional[str],
    description: Optional[str],
    category: Optional[str] = None,
    score: Optional[int] = None,
) -> bool:
    """Update only empty fields with new values (including category, score)."""
    updates: List[str] = []
    params: List[Any] = []
    if score is not None and (score < 1 or score > 3):
        score = None
    for field, new_val in [
        ("sector", sector),
        ("email", email),
        ("phone", phone),
        ("url", url),
        ("description", description),
        ("category", category),
        ("score", score),
    ]:
        cur = existing.get(field)
        is_empty = cur is None or (isinstance(cur, str) and cur.strip() == "")
        has_new = new_val is not None and (not isinstance(new_val, str) or new_val.strip() != "")
        if is_empty and has_new:
            updates.append(f"{field} = %s")
            params.append(new_val)
    if not updates:
        return True
    params.append(id_company)
    res = execute_query(
        "UPDATE company SET " + ", ".join(updates) + " WHERE id_company = %s",
        tuple(params),
        fetch=False,
    )
    return res is True


def _get_first_user_id() -> Optional[int]:
    """Return id_user of the first user for use when no user_id is provided (e.g. for scraping_logs FK)."""
    rows = execute_query("SELECT id_user FROM users ORDER BY id_user LIMIT 1", ())
    if rows and len(rows) > 0:
        return int(rows[0]["id_user"])
    return None


def insert_scraping_log(
    id_user: int,
    source: str,
    parameters: Dict[str, Any],
    total_found: int,
    total_new: int,
    total_updated: int,
    total_failed: int,
    execution_status: str,
    error_message: Optional[str],
    duration_second: Optional[int],
) -> None:
    """
    Insert one row into scraping_logs. executed_at uses DB default.
    Uses INSERT ... RETURNING * to confirm insert; prints row and DB info for debugging.
    Raises if the INSERT fails (e.g. FK violation); errors are not silenced.
    """
    db_info = get_db_info()
    print(f"[scraping_log] DB backend usa: host={db_info['host']} port={db_info['port']} database={db_info['database']}")

    params_json = json.dumps(parameters) if parameters else "{}"
    rows = execute_query(
        """
        INSERT INTO scraping_logs (id_user, source, parameters, total_found, total_new, total_updated, total_failed, execution_status, error_message, duration_second)
        VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        (
            id_user,
            source,
            params_json,
            total_found,
            total_new,
            total_updated,
            total_failed,
            execution_status,
            error_message,
            duration_second,
        ),
        fetch=True,
    )
    if not rows or len(rows) != 1:
        raise RuntimeError(
            f"INSERT scraping_log did not return a row (RETURNING *): rows={rows!r}"
        )
    inserted = dict(rows[0])
    print(f"[scraping_log] INSERT OK: id_scraping={inserted.get('id_scraping')} source={source} execution_status={execution_status}")

QUERY_SYNONYMS = {
    "python": ["python", "django", "flask", "fastapi"],
    "react": ["react", "react.js", "frontend", "javascript", "typescript"],
    "javascript": ["javascript", "js", "typescript", "node", "node.js", "react", "vue", "angular"],
    "qa": ["qa", "quality assurance", "testing", "test engineer", "automation tester", "selenium", "playwright"],
    "devops": ["devops", "dev ops", "sre", "site reliability", "docker", "kubernetes", "aws", "linux"],
    "data": ["data", "data analyst", "data engineer", "data scientist", "etl", "elt", "sql", "pandas", "analytics"],
    "ai": ["ai", "artificial intelligence", "machine learning", "ml", "llm", "genai", "openai", "langchain"],
    "automation": ["automation", "workflow automation", "process automation", "n8n", "zapier", "make", "power automate"],
    "backend": ["backend", "back-end", "server-side", "api", "python", "java", "node", "fastapi", "spring"],
    "frontend": ["frontend", "front-end", "react", "vue", "angular", "javascript", "typescript", "ui"],
}

def run_scraping(
    parameters: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Orchestrator: run scraper, normalize, deduplicate against PostgreSQL,
    insert/update company, then insert scraping_log. Returns public result dict.
    """
    t0 = time.perf_counter()
    totals = {"total_found": 0, "total_new": 0, "total_updated": 0, "total_failed": 0}
    errors: List[str] = []

    if not parameters:
        parameters = {"source": "example_source"}
    source_name = parameters.get("source") or "example_source"

    # Resolve user_id for scraping_logs (required by FK). Always record a log.
    effective_user_id = user_id if user_id is not None else _get_first_user_id()
    if effective_user_id is None:
        raise RuntimeError(
            "Cannot record scraping_log: no user_id provided and no users in database."
        )

    # 1) Execute scraper for the selected source
    try:
        scraper = SCRAPERS.get(source_name)
        if scraper is None:
            raise ValueError(f"Unknown source: {source_name}")
        companies = scraper()
    except Exception as e:
        totals["total_found"] = 0
        totals["total_failed"] = 1
        duration = time.perf_counter() - t0
        execution_status = "FAILED"
        insert_scraping_log(
            id_user=effective_user_id,
            source=source_name,
            parameters=parameters,
            total_found=0,
            total_new=0,
            total_updated=0,
            total_failed=1,
            execution_status=execution_status,
            error_message=str(e),
            duration_second=int(round(duration)),
        )
        result = {
            "total_found": 0,
            "total_new": 0,
            "total_updated": 0,
            "total_failed": 1,
            "execution_status": execution_status,
        }
        if debug:
            result["errors"] = [f"scrape_error: {repr(e)}"]
        return result

    only_riwi_relevant = parameters.get("only_riwi_relevant", True)
    require_junior_focus = parameters.get("require_junior_focus", False)
    max_items = parameters.get("max_items", 20)
    query = (parameters.get("query") or "").strip().lower()

    # Apply query filter first (keyword/synonym match), then cap by max_items
    filtered_companies = []
    for raw in companies:
        raw_job_preview = {
            "job_title": raw.get("job_title") or raw.get("position") or raw.get("title"),
            "job_category": raw.get("job_category") or raw.get("category"),
            "job_description": raw.get("job_description") or raw.get("description"),
            "tags": raw.get("tags") or raw.get("technologies"),
        }

        if query:
            searchable_text = " ".join([
                str(raw_job_preview.get("job_title") or ""),
                str(raw_job_preview.get("job_category") or ""),
                str(raw_job_preview.get("job_description") or ""),
                " ".join(raw_job_preview.get("tags") or []) if isinstance(raw_job_preview.get("tags"), list) else str(raw_job_preview.get("tags") or "")
            ]).lower()


            terms = QUERY_SYNONYMS.get(query, [query])

            matched = False
            for term in terms:
                pattern = r"\b" + re.escape(term.lower()) + r"\b"
                if re.search(pattern, searchable_text, re.IGNORECASE):
                    matched = True
                    break

            if not matched:
                continue


        filtered_companies.append(raw)

    if isinstance(max_items, int) and max_items > 0:
        filtered_companies = filtered_companies[:max_items]

    totals["total_found"] = len(filtered_companies)

    for idx, raw in enumerate(filtered_companies):
        
        try:
            raw_job = {
                "company_name": raw.get("name"),
                "job_title": raw.get("job_title") or raw.get("position") or raw.get("title"),
                "job_category": raw.get("job_category") or raw.get("category"),
                "job_description": raw.get("job_description") or raw.get("description"),
                "tags": raw.get("tags") or raw.get("technologies"),
                "technologies": raw.get("technologies"),
                "source": raw.get("source"),
            }

            # Rule-based filter: skip jobs that are not relevant for Riwi (e.g. marketing, sales)
            if only_riwi_relevant and not job_filters.is_riwi_relevant_job(
                raw_job,
                only_riwi_relevant=True,
                require_junior_focus=require_junior_focus,
            ):
                continue

            profile = job_filters.extract_profile_from_job(raw_job)
            tech_names = job_filters.extract_technologies_from_job(raw_job)
            score: Optional[int] = None
            # AI classification: relevance, profile, score 1–3, technologies; fallback to rules if API fails
            try:
                ai_result = job_classifier.classify_job_with_ai(raw_job)
            except Exception:
                ai_result = None

            if ai_result is not None:
                if not ai_result.get("is_relevant"):
                    continue
                profile = ai_result.get("profile") or profile
                raw_score = ai_result.get("score")
                if raw_score is not None:
                    try:
                        score = int(raw_score)
                        if score not in (1, 2, 3):
                            score = None
                    except (TypeError, ValueError):
                        score = None
                else:
                    score = None
                if ai_result.get("technologies"):
                    tech_names = [str(t).strip().lower() for t in ai_result["technologies"] if t]
                print("AI RESULT:", ai_result)
                print("PROFILE:", profile, "SCORE:", score, "TECHS:", tech_names[:5] if tech_names else [])
            tech_names = list(dict.fromkeys(tech_names))

            # Normalize and deduplicate: find existing company by NIT or (country, name_normalization)
            safe = _safe_company_contract(raw)
            name_norm = normalizer.normalize_name(safe.get("name"))
            safe["name_normalization"] = name_norm
            dedupe_key = normalizer.generate_dedupe_key(safe)
            safe["dedupe_key"] = dedupe_key
            nit_clean = _normalize_nit(safe.get("nit")) or None
            country_val = (safe.get("country") or "").strip() or None
            existing = find_existing_company(nit_clean, country_val, name_norm)

            if existing:
                update_company(
                    id_company=existing["id_company"],
                    existing=existing,
                    sector=safe.get("sector"),
                    email=safe.get("email"),
                    phone=safe.get("phone"),
                    url=safe.get("url"),
                    description=None,
                    category=profile,
                    score=score,
                )
                id_company = existing["id_company"]
                totals["total_updated"] += 1
            else:
                id_company = insert_company(
                    nit=nit_clean or safe.get("nit"),
                    name=safe.get("name") or "",
                    name_normalization=name_norm,
                    sector=safe.get("sector"),
                    email=safe.get("email"),
                    phone=safe.get("phone"),
                    url=safe.get("url"),
                    country=country_val,
                    description=None,
                    category=profile,
                    score=score,
                )
                if id_company is not None:
                    totals["total_new"] += 1
                else:
                    totals["total_failed"] += 1
                    errors.append(f"item_{idx}_insert_failed")
                    continue

            # Persist technologies and link them to this company (technologies + company_technologies)
            for tech_name in tech_names:
                norm = normalize_technology_name(tech_name)
                if not norm:
                    continue
                id_tech = upsert_technology(tech_name)
                if id_tech is not None:
                    link_company_technology(id_company, id_tech)
        except Exception as e:
            totals["total_failed"] += 1
            errors.append(f"item_{idx}_error: {repr(e)}")

    failed = totals["total_failed"]
    found = totals["total_found"]
    if failed == 0:
        execution_status = "SUCCESS"
    elif 0 < failed < found:
        execution_status = "PARTIAL"
    else:
        execution_status = "FAILED"

    duration = time.perf_counter() - t0
    insert_scraping_log(
        id_user=effective_user_id,
        source=source_name,
        parameters=parameters,
        total_found=totals["total_found"],
        total_new=totals["total_new"],
        total_updated=totals["total_updated"],
        total_failed=totals["total_failed"],
        execution_status=execution_status,
        error_message="; ".join(errors) if errors else None,
        duration_second=int(round(duration)),
    )

    result: Dict[str, Any] = {
        "total_found": totals["total_found"],
        "total_new": totals["total_new"],
        "total_updated": totals["total_updated"],
        "total_failed": totals["total_failed"],
        "execution_status": execution_status,
    }
    if debug:
        result["errors"] = errors
    return result
