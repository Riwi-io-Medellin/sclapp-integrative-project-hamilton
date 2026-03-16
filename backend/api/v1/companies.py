"""Companies list and filters."""

from fastapi import APIRouter, Query

from backend.db.connection import execute_query

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/top")
def get_companies_top():
    """Top 10 companies by score DESC, then created_at DESC."""
    rows = execute_query(
        """
        SELECT id_company, name, category, score, country
        FROM company
        WHERE score IS NOT NULL
        ORDER BY score DESC, created_at DESC
        LIMIT 10
        """
    )
    if not rows:
        return []
    return [dict(r) for r in rows]


@router.get("/technologies/trending")
def get_technologies_trending():
    """Top 10 technologies by number of companies using them."""
    rows = execute_query(
        """
        SELECT t.name_tech, COUNT(ct.id_company) AS companies_using
        FROM technologies t
        JOIN company_technologies ct ON ct.id_tech = t.id_tech
        GROUP BY t.id_tech, t.name_tech
        ORDER BY companies_using DESC
        LIMIT 10
        """
    )
    if not rows:
        return []
    return [{"name_tech": r["name_tech"], "companies_using": int(r["companies_using"])} for r in rows]


@router.get("/enriched")
def get_companies_enriched(
    tech: str | None = Query(None),
    score: str | None = Query(None),
    search: str | None = Query(None),
):
    """Companies with aggregated technologies for frontend table."""
    base_sql = """
        SELECT c.id_company, c.name, c.category, c.score, c.country,
               COALESCE(
                 (SELECT STRING_AGG(t.name_tech, ', ' ORDER BY t.name_tech)
                  FROM company_technologies ct
                  JOIN technologies t ON t.id_tech = ct.id_tech
                  WHERE ct.id_company = c.id_company),
                 ''
               ) AS technologies
        FROM company c
        WHERE 1=1
    """
    params = []
    if search:
        base_sql += " AND c.name ILIKE %s"
        params.append(f"%{search}%")
    if tech:
        base_sql += """ AND EXISTS (
            SELECT 1 FROM company_technologies ct
            JOIN technologies t ON t.id_tech = ct.id_tech
            WHERE ct.id_company = c.id_company AND t.name_tech ILIKE %s
        )"""
        params.append(f"%{tech}%")
    if score:
        base_sql += " AND c.score::text = %s"
        params.append(score)
    base_sql += " ORDER BY c.score DESC NULLS LAST, c.created_at DESC LIMIT 500"
    rows = execute_query(base_sql, tuple(params) if params else None)
    if not rows:
        return []
    return [dict(r) for r in rows]


@router.get("")
def get_companies(
    tech: str | None = Query(None, description="Filter by technology"),
    score: str | None = Query(None, description="Filter by AI score"),
    search: str | None = Query(None, description="Search by company name"),
):
    """Return companies with optional filters. Maps DB columns to frontend shape."""
    base_sql = """
        SELECT c.id_company, c.name, c.sector, c.email, c.country,
               c.score,
               (SELECT string_agg(t.name_tech, ', ')
                FROM company_technologies ct
                JOIN technologies t ON t.id_tech = ct.id_tech
                WHERE ct.id_company = c.id_company) AS tech
        FROM company c
        WHERE 1=1
    """
    params = []
    if search:
        base_sql += " AND c.name ILIKE %s"
        params.append(f"%{search}%")
    if tech:
        base_sql += """ AND EXISTS (
            SELECT 1 FROM company_technologies ct
            JOIN technologies t ON t.id_tech = ct.id_tech
            WHERE ct.id_company = c.id_company AND t.name_tech ILIKE %s
        )"""
        params.append(f"%{tech}%")
    if score:
        base_sql += " AND c.score::text = %s"
        params.append(score)

    base_sql += " ORDER BY c.name LIMIT 500"
    rows = execute_query(base_sql, tuple(params) if params else None)
    if not rows:
        return []

    def map_row(r):
        labels = {3: "Alta", 2: "Media", 1: "Baja"}
        score_label = labels.get(r.get("score"), "Sin asignar")
        return {
            "id_company": r["id_company"],
            "name": r["name"],
            "nombre": r["name"],
            "tech": r["tech"] or "—",
            "technologies": r["tech"] or "—",
            "nivel": "—",
            "level": "—",
            "ciudad": r.get("country") or "—",
            "city": r.get("country") or "—",
            "location": r.get("country") or "—",
            "score": score_label,
            "ai_score": score_label,
        }

    return [map_row(dict(row)) for row in rows]
