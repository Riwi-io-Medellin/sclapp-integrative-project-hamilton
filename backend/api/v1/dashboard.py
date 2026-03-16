"""Dashboard metrics and AI report."""

from fastapi import APIRouter

from backend.db.connection import execute_query

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
    """AI-generated report items for the dashboard (placeholder or real AI later)."""
    return {
        "items": [
            {
                "icon": "📊",
                "title": "Positive trend:",
                "description": "Companies using React and Python have a 34% higher probability of hiring junior talent.",
            },
            {
                "icon": "🎯",
                "title": "Recommendation:",
                "description": "Prioritize fintech startups — 3x higher reply rate than enterprise companies.",
            },
            {
                "icon": "⚡",
                "title": "Opportunity:",
                "description": '18 companies in "Negotiation" have had no follow-up for more than 5 days. Re-contact is recommended.',
            },
        ]
    }
