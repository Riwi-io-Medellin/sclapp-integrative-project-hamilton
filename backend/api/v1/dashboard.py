"""Dashboard metrics and AI report."""

from fastapi import APIRouter

from backend.db.connection import execute_query
from backend.services.ai.dashboard_report import generate_dashboard_ai_report

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats():
    """Stats for KPIs: total_companies, scored_companies, high_score_companies, emails_sent."""
    total = execute_query("SELECT COUNT(*) AS c FROM company")
    scored = execute_query("SELECT COUNT(*) AS c FROM company WHERE score IS NOT NULL")
    high = execute_query("SELECT COUNT(*) AS c FROM company WHERE score = 3")
    emails = execute_query("SELECT COUNT(*) AS c FROM emails WHERE send_status = 'sent'")

    def n(q, default=0):
        return int(q[0]["c"]) if q and len(q) > 0 else default

    return {
        "total_companies": n(total),
        "scored_companies": n(scored),
        "high_score_companies": n(high),
        "emails_sent": n(emails),
    }


@router.get("/metrics")
def get_dashboard_metrics():
    """Aggregate counts for KPI cards and charts."""
    total_companies = execute_query("SELECT COUNT(*) AS count FROM company")
    emails_sent = execute_query("SELECT COUNT(*) AS count FROM emails WHERE send_status = 'sent'")
    companies_engaged = execute_query(
        "SELECT COUNT(*) AS count FROM company c JOIN statuses s ON s.id_status = c.id_status WHERE s.code IN ('negotiation', 'contacted')"
    )
    open_rate = execute_query(
        "SELECT COUNT(*) AS opened FROM email_events WHERE event_type = 'open'"
    )
    total_sent = execute_query("SELECT COUNT(*) AS total FROM emails WHERE send_status = 'sent'")

    def safe_count(q, default=0):
        return q[0]["count"] if q else default

    total_sent_val = safe_count(total_sent)
    opened_val = safe_count(open_rate)
    rate = (opened_val / total_sent_val * 100) if total_sent_val else 0

    return {
        "companies_with_vacancies": safe_count(total_companies),
        "emails_sent": safe_count(emails_sent),
        "companies_engaged": safe_count(companies_engaged),
        "open_rate_percent": round(rate, 1),
        "trend_companies": "+12.5",
        "trend_emails": "+8.3",
        "trend_engaged": "+23.1",
        "trend_open_rate": "-2.1",
    }


@router.get("/ai-report")
def get_ai_report():
    """
    Endpoint AI para el dashboard.

    Devuelve un JSON con:
    {
      "summary": str,
      "highlights": [str, ...],
      "recommendation": str
    }

    Usa métricas reales de la DB y OpenAI si está configurado; si falla, devuelve un fallback útil
    basado en los mismos datos reales para no romper la UI.
    """
    return generate_dashboard_ai_report()


@router.get("/score-distribution")
def get_score_distribution():
    """
    Distribución global de empresas con score asignado.

    Retorna:
    {
      "high": number,    # score = 3
      "medium": number,  # score = 2
      "low": number,     # score = 1
      "total_scored": number  # score IS NOT NULL
    }
    """
    row = execute_query(
        """
        SELECT
          SUM(CASE WHEN score = 3 THEN 1 ELSE 0 END) AS high,
          SUM(CASE WHEN score = 2 THEN 1 ELSE 0 END) AS medium,
          SUM(CASE WHEN score = 1 THEN 1 ELSE 0 END) AS low,
          SUM(CASE WHEN score IS NOT NULL THEN 1 ELSE 0 END) AS total_scored
        FROM company
        """
    )

    if not row:
        return {"high": 0, "medium": 0, "low": 0, "total_scored": 0}

    r = row[0]
    return {
        "high": int(r.get("high") or 0),
        "medium": int(r.get("medium") or 0),
        "low": int(r.get("low") or 0),
        "total_scored": int(r.get("total_scored") or 0),
    }
